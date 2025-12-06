import secrets, uuid
from datetime import datetime, timedelta
from fastapi import HTTPException
from utils.crypto import verify_signature
from utils.jwt import create_access_token
import logging
from config.database import get_collection

logger = logging.getLogger(__name__)
auth_db = get_collection("collection_auth_challenges")
users_db = get_collection("collection_users")


# -----------------------------------------------------
# CREATE CHALLENGE
# -----------------------------------------------------
async def create_challenge(wallet_address: str):
    logger.info(f"Creating challenge for wallet={wallet_address}")

    challenge = "nonce_" + secrets.token_hex(12)
    expires_at = (datetime.utcnow() + timedelta(minutes=5)).isoformat() + "Z"

    # dữ liệu update KHÔNG chứa _id
    update_doc = {
        "wallet_address": wallet_address,
        "challenge": challenge,
        "expires_at": expires_at,
        "used": False,
        "created_at": datetime.utcnow().isoformat() + "Z"
    }

    # Upsert theo wallet_address
    await auth_db.update_one(
        {"wallet_address": wallet_address},
        {"$set": update_doc},
        upsert=True
    )

    return challenge, expires_at



# -----------------------------------------------------
# VERIFY USER
# -----------------------------------------------------
async def verify_user(wallet_address: str, signature: str):
    record = await auth_db.find_one({"wallet_address": wallet_address})

    if not record:
        raise HTTPException(status_code=400, detail="No challenge found for this wallet")
    if record.get("used"):
        raise HTTPException(status_code=400, detail="Challenge already used")

    # Check expired
    if datetime.fromisoformat(record["expires_at"].replace("Z", "")) < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Challenge expired")

    # Verify signature
    if not verify_signature(wallet_address, record["challenge"], signature):
        raise HTTPException(status_code=401, detail="Invalid signature")

    # Mark as used (KHÔNG update _id)
    await auth_db.update_one(
        {"wallet_address": wallet_address},
        {"$set": {"used": True}}
    )

    # Ensure user exists
    user = await users_db.find_one({"wallet_address": wallet_address})

    if not user:
        user = {
            "_id": f"user_{uuid.uuid4().hex}",
            "wallet_address": wallet_address,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "display_name": f"user_{wallet_address[:6]}",
            "roles": ["user"]
        }

        # insert mới
        await users_db.insert_one(user)

    access_token = create_access_token(user["_id"], wallet_address)

    return user, access_token

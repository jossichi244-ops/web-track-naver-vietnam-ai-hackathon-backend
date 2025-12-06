import secrets, uuid
from datetime import datetime, timedelta
from fastapi import HTTPException
from utils.jsondb import JsonDB
from utils.crypto import verify_signature
from utils.jwt import create_access_token
import logging
from config.database import get_collection

logger = logging.getLogger(__name__)
auth_db = get_collection("collection_auth_challenges")
users_db = get_collection("collection_users")

def create_challenge(wallet_address: str):
    logger.info(f"Creating challenge for wallet={wallet_address}")
    challenge = "nonce_" + secrets.token_hex(12)
    expires_at = (datetime.utcnow() + timedelta(minutes=5)).isoformat() + "Z"

    doc = {
        "_id": f"chal_{uuid.uuid4().hex}",
        "wallet_address": wallet_address,
        "challenge": challenge,
        "expires_at": expires_at,
        "used": False,
        "created_at": datetime.utcnow().isoformat() + "Z"
    }
    auth_db.insert_or_replace("wallet_address", wallet_address, doc)
    return challenge, expires_at

def verify_user(wallet_address: str, signature: str):
    record = auth_db.find_one("wallet_address", wallet_address)
    if not record:
        raise HTTPException(status_code=400, detail="No challenge found for this wallet")
    if record["used"]:
        raise HTTPException(status_code=400, detail="Challenge already used")
    if datetime.fromisoformat(record["expires_at"].replace("Z", "")) < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Challenge expired")

    ok = verify_signature(wallet_address, record["challenge"], signature)
    if not ok:
        raise HTTPException(status_code=401, detail="Invalid signature")

    record["used"] = True
    auth_db.insert_or_replace("wallet_address", wallet_address, record)

    # Ensure user exists
    user = users_db.find_one("wallet_address", wallet_address)
    if not user:
        user = {
            "_id": f"user_{uuid.uuid4().hex}",
            "wallet_address": wallet_address,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "display_name": f"user_{wallet_address[:6]}",
            "roles": ["user"]
        }
        users_db.insert_or_replace("wallet_address", wallet_address, user)

    access_token = create_access_token(user["_id"], wallet_address)

    return user, access_token
import uuid
from datetime import datetime
from fastapi import HTTPException
from typing import Optional, List
from config.database import get_collection

challenges_db = get_collection("collection_community_challenges")


def _format_datetime(dt: datetime) -> str:
    if dt.tzinfo is None:
        return dt.isoformat() + "Z"
    else:
        return dt.isoformat().replace("+00:00", "Z")


# =======================================
# CREATE
# =======================================
async def create_challenge(data: dict, user_id: str, wallet_address: str) -> dict:
    challenge_id = f"chal_{uuid.uuid4().hex}"
    now = _format_datetime(datetime.utcnow())

    challenge = {
        "_id": challenge_id,
        "user_id": user_id,
        "wallet_address": wallet_address,
        "shared_at": now,
        **data
    }

    await challenges_db.insert_one(challenge)
    return challenge


# =======================================
# GET ONE
# =======================================
async def get_challenge(challenge_id: str) -> dict:
    challenge = await challenges_db.find_one({"_id": challenge_id})
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")
    return challenge


# =======================================
# UPDATE
# =======================================
async def update_challenge(challenge_id: str, updates: dict, requester_wallet_address: str) -> dict:
    challenge = await get_challenge(challenge_id)

    if challenge["wallet_address"] != requester_wallet_address:
        raise HTTPException(status_code=403, detail="Only owner can update challenge")

    # Xóa các field không được phép update
    protected = ["_id", "user_id", "wallet_address", "shared_at"]
    for key in protected:
        updates.pop(key, None)

    if not updates:
        return challenge

    await challenges_db.update_one(
        {"_id": challenge_id},
        {"$set": updates}
    )

    return await get_challenge(challenge_id)


# =======================================
# DELETE
# =======================================
async def delete_challenge(challenge_id: str, requester_wallet_address: str) -> dict:
    challenge = await get_challenge(challenge_id)

    if challenge["wallet_address"] != requester_wallet_address:
        raise HTTPException(status_code=403, detail="Only owner can delete challenge")

    await challenges_db.delete_one({"_id": challenge_id})

    return {"status": "deleted", "challenge_id": challenge_id}


# =======================================
# LIST / FILTER
# =======================================
async def list_challenges(
    wallet_address: Optional[str] = None,
    user_id: Optional[str] = None,
    tags: Optional[List[str]] = None
) -> list:

    query = {}

    if wallet_address:
        query["wallet_address"] = wallet_address

    if user_id:
        query["user_id"] = user_id

    if tags:
        query["tags"] = {"$in": tags}

    cursor = challenges_db.find(query)
    return await cursor.to_list(length=None)

import uuid
from datetime import datetime
from fastapi import HTTPException
from typing import Optional, List
from utils.jsondb import JsonDB

challenges_db = JsonDB("db/collection_community_challenges.json")


def _format_datetime(dt: datetime) -> str:
    if dt.tzinfo is None:
        return dt.isoformat() + "Z"
    else:
        return dt.isoformat().replace("+00:00", "Z")


def create_challenge(data: dict, user_id: str, wallet_address: str) -> dict:
    """Tạo chia sẻ mới (challenge)"""
    challenge_id = f"chal_{uuid.uuid4().hex}"
    now = _format_datetime(datetime.utcnow())

    challenge = {
        "_id": challenge_id,
        "user_id": user_id,
        "wallet_address": wallet_address,
        "shared_at": now,
        **data
    }

    challenges_db.insert_or_replace("_id", challenge_id, challenge)
    return challenge


def get_challenge(challenge_id: str) -> dict:
    """Lấy thông tin challenge"""
    challenge = challenges_db.find_one("_id", challenge_id)
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")
    return challenge


def update_challenge(challenge_id: str, updates: dict, requester_wallet_address: str) -> dict:
    """Cập nhật challenge — chỉ người chia sẻ (owner) mới có quyền"""
    challenge = get_challenge(challenge_id)

    if challenge["wallet_address"] != requester_wallet_address:
        raise HTTPException(status_code=403, detail="Only owner can update challenge")

    # Không cho update user_id hoặc wallet_address
    for key in ["user_id", "wallet_address", "shared_at", "_id"]:
        updates.pop(key, None)

    challenge.update({k: v for k, v in updates.items() if v is not None})
    challenges_db.insert_or_replace("_id", challenge_id, challenge)
    return challenge


def delete_challenge(challenge_id: str, requester_wallet_address: str) -> dict:
    """Xóa challenge — chỉ người chia sẻ (owner) mới có quyền"""
    challenge = get_challenge(challenge_id)

    if challenge["wallet_address"] != requester_wallet_address:
        raise HTTPException(status_code=403, detail="Only owner can delete challenge")

    challenges = challenges_db.read_all()
    filtered = [c for c in challenges if c["_id"] != challenge_id]
    challenges_db.write_all(filtered)

    return {"status": "deleted", "challenge_id": challenge_id}


def list_challenges(
    wallet_address: Optional[str] = None,
    user_id: Optional[str] = None,
    tags: Optional[List[str]] = None
) -> list:
    """Liệt kê challenge — có thể lọc theo wallet_address, user_id hoặc tags"""
    challenges = challenges_db.read_all()

    if wallet_address:
        challenges = [c for c in challenges if c["wallet_address"] == wallet_address]

    if user_id:
        challenges = [c for c in challenges if c["user_id"] == user_id]

    if tags:
        challenges = [
            c for c in challenges
            if "tags" in c and any(tag in c["tags"] for tag in tags)
        ]

    return challenges

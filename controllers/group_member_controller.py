# controllers/group_member_controller.py
import uuid
from datetime import datetime
from fastapi import HTTPException, Request
from typing import List
import logging

from config.database import get_collection

members_db = get_collection("collection_group_members")

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


def _format_datetime(dt: datetime) -> str:
    if dt.tzinfo is None:
        return dt.isoformat() + "Z"
    else:
        return dt.isoformat().replace("+00:00", "Z")


def _get_permissions(role: str) -> List[str]:
    if role == "owner":
        return ["*"]

    if role == "admin":
        return [
            "create_task", "edit_task", "delete_task", "assign_task",
            "invite_member", "remove_member", "update_group_info",
            "change_role", "view_task", "create_announcement",
            "pin_task", "archive_task"
        ]

    if role == "member":
        return ["create_task", "edit_task", "view_task", "assign_task"]

    if role == "guest":
        return ["view_task"]

    return ["view_task"]


# ----------------------------------------------------------------
# ADD MEMBER
# ----------------------------------------------------------------
async def add_member(data: dict) -> dict:
    # Avoid circular import
    from controllers.group_controller import get_group

    group = await get_group(data["group_id"])
    role = data.get("role", "member")

    joined_at = (
        group["created_at"] if role == "owner"
        else _format_datetime(datetime.utcnow())
    )

    # Guest cannot join private groups
    if role == "guest" and not group.get("is_public", False):
        raise HTTPException(status_code=403, detail="Cannot join as guest: group is private")

    member_doc = {
        "_id": f"mem_{uuid.uuid4().hex}",
        "group_id": data["group_id"],
        "user_id": data["user_id"],
        "wallet_address": data["wallet_address"].lower(),
        "role": role,
        "joined_at": joined_at,
        "last_active_at": _format_datetime(datetime.utcnow()),
        "permissions": _get_permissions(role),
    }

    await members_db.update_one(
        {"_id": member_doc["_id"]},
        {"$set": member_doc},
        upsert=True
    )

    return member_doc


# ----------------------------------------------------------------
# JOIN PUBLIC GROUP
# ----------------------------------------------------------------
async def join_group(data: dict) -> dict:
    from controllers.group_controller import get_group

    group = await get_group(data["group_id"])

    if not group.get("is_public", False):
        raise HTTPException(status_code=403, detail="Group is private. Cannot join directly.")

    now = _format_datetime(datetime.utcnow())

    member_doc = {
        "_id": f"mem_{uuid.uuid4().hex}",
        "group_id": data["group_id"],
        "user_id": data["user_id"],
        "wallet_address": data["wallet_address"].lower(),
        "role": "guest",
        "joined_at": now,
        "last_active_at": now,
        "permissions": _get_permissions("guest"),
    }

    await members_db.update_one(
        {"_id": member_doc["_id"]},
        {"$set": member_doc},
        upsert=True
    )

    return member_doc


# ----------------------------------------------------------------
# GET MEMBERS OF A GROUP
# ----------------------------------------------------------------
async def get_members(group_id: str, current_user: dict) -> List[dict]:
    members = await members_db.find({"group_id": group_id}).to_list(None)
    return members


# ----------------------------------------------------------------
# UPDATE MEMBER BY WALLET
# ----------------------------------------------------------------
async def update_member_by_wallet(group_id: str, request: Request, updates: dict) -> dict:
    logger.debug(f"Incoming update for group_id={group_id}: {updates}")

    wallet_address = request.query_params.get("wallet_address")
    if not wallet_address:
        raise HTTPException(status_code=400, detail="wallet_address is required in query parameters")

    normalized_wallet = wallet_address.lower()

    member = await members_db.find_one({
        "group_id": group_id,
        "wallet_address": normalized_wallet
    })

    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    logger.debug(f"Found member: {member}")

    updates["last_active_at"] = _format_datetime(datetime.utcnow())

    if "role" in updates:
        updates["permissions"] = _get_permissions(updates["role"])

    await members_db.update_one(
        {"_id": member["_id"]},
        {"$set": updates}
    )

    updated_member = await members_db.find_one({"_id": member["_id"]})
    return updated_member


# ----------------------------------------------------------------
# REMOVE MEMBER
# ----------------------------------------------------------------
async def remove_member(member_id: str) -> dict:
    result = await members_db.delete_one({"_id": member_id})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Member not found")

    return {"status": "deleted", "member_id": member_id}
# ----------------------------------------------------------------
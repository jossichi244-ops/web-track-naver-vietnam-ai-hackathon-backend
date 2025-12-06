# controllers/group_member_controller.py
import uuid
from datetime import datetime
from fastapi import HTTPException, Request
from utils.jsondb import JsonDB
from controllers.group_controller import get_group
from config.database import get_collection
# from utils import _format_datetime, _get_permissions
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Đảm bảo cấp độ log đủ chi tiết (DEBUG hoặc INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

members_db = get_collection("collection_group_members")

def _format_datetime(dt: datetime) -> str:
    if dt.tzinfo is None:
        return dt.isoformat() + "Z"
    else:
        return dt.isoformat().replace("+00:00", "Z")

def _get_permissions(role: str) -> list[str]:
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
        return [
    "create_task", "edit_task", "view_task",
    "assign_task"
]

    if role == "guest":
        return ["view_task"]
    return ["view_task"]

def add_member(data: dict) -> dict:
    """Thêm thành viên vào nhóm"""

    # ✅ Tránh circular import bằng cách import tại đây
    from controllers.group_controller import get_group

    group = get_group(data["group_id"])
    role = data.get("role", "member")

    if role == "owner":
        joined_at = group["created_at"]
    else:
        joined_at = _format_datetime(datetime.utcnow())

    if role == "guest" and not group.get("is_public", False):
        raise HTTPException(status_code=403, detail="Cannot join as guest: group is private")

    member = {
        "_id": f"mem_{uuid.uuid4().hex}",
        "group_id": data["group_id"],
        "user_id": data["user_id"],
        "wallet_address": data["wallet_address"],
        "role": role,
        "joined_at": joined_at,
        "last_active_at": _format_datetime(datetime.utcnow()),
        "permissions": _get_permissions(role),
    }

    members_db.insert_or_replace("_id", member["_id"], member)
    return member

def join_group(data: dict) -> dict:
    """Người dùng tự join group"""

    # ✅ Import tại đây để tránh vòng lặp
    from controllers.group_controller import get_group

    group = get_group(data["group_id"])
    now = _format_datetime(datetime.utcnow())

    if not group.get("is_public", False):
        raise HTTPException(status_code=403, detail="Group is private. Cannot join directly.")

    member = {
        "_id": f"mem_{uuid.uuid4().hex}",
        "group_id": data["group_id"],
        "user_id": data["user_id"],
        "wallet_address": data["wallet_address"],
        "role": "guest",
        "joined_at": now,
        "last_active_at": now,
        "permissions": _get_permissions("guest"),
    }

    members_db.insert_or_replace("_id", member["_id"], member)
    return member

def get_members(group_id: str, current_user: dict) -> list[dict]:
    """Lấy danh sách thành viên của group nếu user thuộc group đó"""
    members = members_db.read_all()

    return [m for m in members if m.get("group_id") == group_id]


# def update_member(member_id: str, updates: dict) -> dict:
#     member = members_db.find_one("_id", member_id)
#     if not member:
#         raise HTTPException(status_code=404, detail="Member not found")

#     # Update last_active_at khi có hoạt động
#     updates["last_active_at"] = _format_datetime(datetime.utcnow())

#     if "role" in updates:
#         updates["permissions"] = _get_permissions(updates["role"])

#     member.update({k: v for k, v in updates.items() if v is not None})
#     members_db.insert_or_replace("_id", member_id, member)
#     return member

async def update_member_by_wallet(group_id: str, request: Request, updates: dict) -> dict:
    # Log the incoming request to understand what data is being passed
    logger.debug(f"Incoming request data for group_id={group_id}: {updates}")

    # Retrieve the wallet_address from the query parameter
    wallet_address = request.query_params.get('wallet_address')
    logger.debug(f"Extracted wallet_address from query params: {wallet_address}")

    if not wallet_address:
        logger.error("No wallet_address provided in query parameters.")
        raise HTTPException(status_code=400, detail="wallet_address is required in the query parameters")

    normalized_wallet = wallet_address.lower()  # Normalize the wallet address
    logger.debug(f"Normalized wallet address: {normalized_wallet}")

    # Try to find the member based on the group_id and wallet_address
    member = members_db.find_one({
        "group_id": group_id,
        "wallet_address": normalized_wallet
    })

    if not member:
        logger.error(f"Member not found for group_id: {group_id}, wallet_address: {normalized_wallet}")
        raise HTTPException(status_code=404, detail="Member not found")

    # Log the found member details before applying any changes
    logger.debug(f"Found member: {member}")

    # Update the member's details (e.g., role, permissions)
    updates["last_active_at"] = _format_datetime(datetime.utcnow())  # Always update last_active_at
    logger.debug(f"Updated 'last_active_at': {updates['last_active_at']}")

    if "role" in updates:
        updates["permissions"] = _get_permissions(updates["role"])
        logger.debug(f"Updated permissions: {updates['permissions']}")

    # Apply the updates to the member object
    member.update({k: v for k, v in updates.items() if v is not None})
    logger.debug(f"Updated member data: {member}")

    # Save the updated member data to the database
    members_db.insert_or_replace("_id", member["_id"], member)
    logger.info(f"Successfully updated member with _id: {member['_id']}")

    return member
def remove_member(member_id: str) -> dict:
    members = members_db.read_all()
    filtered = [m for m in members if m["_id"] != member_id]
    members_db.write_all(filtered)
    return {"status": "deleted", "member_id": member_id}

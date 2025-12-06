# controllers/group_controller.py
import uuid
from datetime import datetime
from fastapi import HTTPException
from typing import Optional, List
from config.database import get_collection

groups_db = get_collection("collection_groups")
group_members_db = get_collection("collection_group_members")


def _format_datetime(dt: datetime) -> str:
    if dt.tzinfo is None:
        return dt.isoformat() + "Z"
    else:
        return dt.isoformat().replace("+00:00", "Z")


# ------------------------------
# CREATE GROUP
# ------------------------------
async def create_group(data: dict, user_id: str, wallet_address: str) -> dict:
    group_id = f"grp_{uuid.uuid4().hex}"
    now = _format_datetime(datetime.utcnow())

    group_doc = {
        "_id": f"grpdoc_{uuid.uuid4().hex}",
        "group_id": group_id,
        "wallet_address": wallet_address,
        "created_at": now,
        "updated_at": now,
        **data
    }

    # Insert group
    await groups_db.update_one(
        {"group_id": group_id},
        {"$set": group_doc},
        upsert=True
    )

    # Auto add owner as member
    owner_member = {
        "_id": f"mem_{uuid.uuid4().hex}",
        "group_id": group_id,
        "user_id": user_id,
        "wallet_address": wallet_address,
        "role": "owner",
        "joined_at": now,
        "last_active_at": now,
        "permissions": ["*"]
    }

    await group_members_db.update_one(
        {"_id": owner_member["_id"]},
        {"$set": owner_member},
        upsert=True
    )

    return group_doc


# ------------------------------
# GET GROUP
# ------------------------------
async def get_group(group_id: str) -> dict:
    group = await groups_db.find_one({"group_id": group_id})
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    return group


# ------------------------------
# UPDATE GROUP
# ------------------------------
async def update_group(group_id: str, updates: dict, requester_wallet_address: str) -> dict:
    group = await get_group(group_id)

    if group["wallet_address"] != requester_wallet_address:
        raise HTTPException(status_code=403, detail="Only owner can update group")

    updates["updated_at"] = _format_datetime(datetime.utcnow())

    await groups_db.update_one(
        {"group_id": group_id},
        {"$set": updates}
    )

    return await get_group(group_id)


# ------------------------------
# DELETE GROUP
# ------------------------------
async def delete_group(group_id: str, requester_wallet_address: str) -> dict:
    group = await get_group(group_id)

    if group["wallet_address"] != requester_wallet_address:
        raise HTTPException(status_code=403, detail="Only owner can delete group")

    await groups_db.delete_one({"group_id": group_id})
    await group_members_db.delete_many({"group_id": group_id})

    return {"status": "deleted", "group_id": group_id}


# ------------------------------
# LIST GROUPS
# ------------------------------
async def list_groups(wallet_address: Optional[str] = None, is_public: Optional[bool] = None) -> list:
    query = {}

    if wallet_address:
        query["wallet_address"] = wallet_address

    if is_public is not None:
        query["is_public"] = is_public

    groups = await groups_db.find(query).to_list(None)
    return groups


# ------------------------------
# LIST GROUPS MULTI OWNER
# ------------------------------
async def list_groups_multi(wallet_addresses: Optional[List[str]] = None,
                            is_public: Optional[bool] = None) -> list:
    
    query = {}

    if wallet_addresses:
        query["wallet_address"] = {"$in": wallet_addresses}

    if is_public is not None:
        query["is_public"] = is_public

    groups = await groups_db.find(query).to_list(None)
    return groups

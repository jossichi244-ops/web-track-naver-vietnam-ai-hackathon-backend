# controllers/group_controller.py
import uuid
from datetime import datetime
from fastapi import HTTPException
from utils.jsondb import JsonDB
from typing import Optional 
from typing import Optional, List
from config.database import get_collection

groups_db = get_collection("collection_groups")
group_members_db = get_collection("collection_group_members")

def _format_datetime(dt: datetime) -> str:
    if dt.tzinfo is None:
        return dt.isoformat() + "Z"
    else:
        return dt.isoformat().replace("+00:00", "Z")

def create_group(data: dict,user_id: str, wallet_address: str) -> dict:
    """Tạo nhóm mới — chỉ owner mới có quyền tạo"""
    group_id = f"grp_{uuid.uuid4().hex}"
    now = _format_datetime(datetime.utcnow())

    group = {
        "_id": f"grpdoc_{uuid.uuid4().hex}",
        "group_id": group_id,
        "wallet_address": wallet_address,
        "created_at": now,
        "updated_at": now,
        **data
    }

    groups_db.insert_or_replace("group_id", group_id, group)

    # ✅ Thêm người tạo vào group_members_db với vai trò 'owner'
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

    group_members_db.insert_or_replace("_id", owner_member["_id"], owner_member)

    return group

def get_group(group_id: str) -> dict:
    """Lấy thông tin nhóm theo group_id"""
    group = groups_db.find_one("group_id", group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    return group

def update_group(group_id: str, updates: dict, requester_wallet_address: str) -> dict:
    """Cập nhật nhóm — chỉ owner mới có quyền"""
    group = get_group(group_id)
    
    if group["wallet_address"] != requester_wallet_address:
        raise HTTPException(status_code=403, detail="Only owner can update group")
    
    # Cập nhật updated_at
    updates["updated_at"] = _format_datetime(datetime.utcnow())
    
    group.update({k: v for k, v in updates.items() if v is not None})
    groups_db.insert_or_replace("group_id", group_id, group)
    return group

def delete_group(group_id: str, requester_wallet_address: str) -> dict:
    """Xóa nhóm — chỉ owner mới có quyền"""
    group = get_group(group_id)
    
    if group["wallet_address"] != requester_wallet_address:
        raise HTTPException(status_code=403, detail="Only owner can delete group")
    
    groups = groups_db.read_all()
    filtered = [g for g in groups if g["group_id"] != group_id]
    groups_db.write_all(filtered)
    return {"status": "deleted", "group_id": group_id}

def list_groups(wallet_address: Optional[str] = None, is_public: Optional[bool] = None) -> list:
    """Liệt kê nhóm — có thể filter theo owner hoặc is_public"""
    groups = groups_db.read_all()
    if wallet_address:
        groups = [g for g in groups if g["wallet_address"] == wallet_address]
    if is_public is not None:
        groups = [g for g in groups if g["is_public"] == is_public]
    return groups

def list_groups_multi(wallet_addresses: Optional[List[str]] = None, is_public: Optional[bool] = None) -> list:
    groups = groups_db.read_all()
    if wallet_addresses:
        groups = [g for g in groups if g["wallet_address"] in wallet_addresses]
    if is_public is not None:
        groups = [g for g in groups if g["is_public"] == is_public]
    return groups
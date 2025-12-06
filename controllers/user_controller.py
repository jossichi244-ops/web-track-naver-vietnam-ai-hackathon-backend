# backend/controllers/user_controller.py
from fastapi import HTTPException
from utils.jsondb import JsonDB
from datetime import datetime
from models.user import ProfileSummary, UserUpdateRequest, UserResponse
from typing import List
from config.database import get_collection
users_db = get_collection("collection_users")
groups_db = get_collection("collection_groups")
group_members_db = get_collection("collection_group_members")
tasks_db = get_collection("collection_tasks")
attachments_db = get_collection("collection_task_attachments")

def get_user(wallet_address: str) -> UserResponse:
    user = users_db.find_one("wallet_address", wallet_address)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    summary, groups_info,all_tasks     = calculate_profile_summary(wallet_address)

    user["profile_summary"] = summary
    user["groups_overview"] = groups_info
    user["total_group_tasks"] = summary["total_tasks"]

    # 👉 thêm dữ liệu group & task
    extra_info = get_user_groups_and_tasks(wallet_address)
    user["groups_overview"] = extra_info["groups"]
    user["total_group_tasks"] = extra_info["total_group_tasks"]
    user["user_tasks"] = all_tasks

    return UserResponse(**user)

def default_summary():
    return {
        "total_tasks": 0,
        "completed_tasks": 0,
        "in_progress_tasks": 0,
        "pending_tasks": 0,
        "productivity_score": 0,
        "last_updated_summary": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

def calculate_profile_summary(wallet_address: str):
    memberships = group_members_db.find_many("wallet_address", wallet_address)
    if not memberships:
        return default_summary(), [], []

    groups_info = []
    all_tasks = []

    for member in memberships:
        group_id = member["group_id"]
        group = groups_db.find_one("group_id", group_id)
        if not group:
            continue

        group_tasks = tasks_db.find_many("group_id", group_id) or []
        all_tasks.extend(group_tasks)

        groups_info.append({
            "group_id": group_id,
            "group_name": group.get("name", ""),
            "role": member.get("role", "member"),
            "task_count": len(group_tasks),
        })

    total = len(all_tasks)
    completed, in_progress, pending = 0, 0, 0

    for t in all_tasks:
        status = t.get("status", "pending")
        if status == "completed" or t.get("is_completed"):
            completed += 1
        elif status == "in_progress":
            in_progress += 1
        else:
            pending += 1

        # Rule: nếu có attachment coi như completed
        task_id = t.get("task_id")
        if task_id:
            attachments = attachments_db.find_many("task_id", task_id)
            if attachments and status != "completed":
                completed += 1
                pending = max(0, pending - 1)
                t["is_completed"] = True  

    productivity_score = (completed / total * 100) if total > 0 else 0

    summary = {
        "total_tasks": total,
        "completed_tasks": completed,
        "in_progress_tasks": in_progress,
        "pending_tasks": pending,
        "productivity_score": productivity_score,
        "last_updated_summary": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    return summary, groups_info, all_tasks

def get_user_groups_and_tasks(wallet_address: str):
    # Lấy tất cả membership record của user
    memberships = group_members_db.find_many("wallet_address", wallet_address)

    if not memberships:
        return {"groups": [], "total_group_tasks": 0}

    groups_info = []
    total_tasks = 0

    for member in memberships:
        group_id = member["group_id"]
        group = groups_db.find_one("group_id", group_id)
        if not group:
            continue

        # Đếm số task trong group này
        group_tasks = tasks_db.find_many("group_id", group_id)
        task_count = len(group_tasks)
        total_tasks += task_count

        groups_info.append({
            "group_id": group_id,
            "group_name": group.get("name", ""),
            "role": member.get("role", "member"),
            "task_count": task_count,
        })

    return {
        "groups": groups_info,
        "total_group_tasks": total_tasks
    }

def update_user(wallet_address: str, updates: UserUpdateRequest) -> UserResponse:
    # Find user in the database
    user = users_db.find_one("wallet_address", wallet_address)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Convert Pydantic model to dict, excluding unset fields
    update_data = updates.dict(exclude_unset=True)
    
    # List of fields that are immutable and should not be updated
    immutable_fields = {
        "wallet_address", "created_at", "profile_summary", "user_tasks", 
        "proficiency_level", "last_used_at", "verified_by_tasks", "endorsed_by"
    }
    
    # Remove any immutable fields from the update request
    for field in immutable_fields:
        if field in update_data:
            del update_data[field]
    
    # Optionally, update preferences if provided
    if "preferences" in update_data:
        current_prefs = user.get("preferences", {})
        current_prefs.update(update_data["preferences"])
        update_data["preferences"] = current_prefs
    
    # Set the last login time if there's an update
    if len(update_data) > 0:
        update_data["last_login"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    
    # Apply the update to the user
    user.update(update_data)
    
    # Ensure profile_summary exists before creating UserResponse
    if "profile_summary" not in user:
        user["profile_summary"] = ProfileSummary(
            total_tasks=0,
            completed_tasks=0,
            in_progress_tasks=0,
            pending_tasks=0,
            productivity_score=0.0,
            last_updated_summary=datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        ).dict()
    
    # Save the updated user back into the DB
    users_db.insert_or_replace("wallet_address", wallet_address, user)
    
    return UserResponse(**user)

def get_all_users() -> List[UserResponse]:
    users = users_db.find_all()
    result = []

    for user in users:
        wallet_address = user.get("wallet_address")
        if not wallet_address:
            continue

        # Tính summary + groups + tasks cho từng user
        summary, groups_info, all_tasks = calculate_profile_summary(wallet_address)

        user["profile_summary"] = summary
        user["groups_overview"] = groups_info
        user["total_group_tasks"] = summary["total_tasks"]
        user["user_tasks"] = all_tasks

        result.append(UserResponse(**user))

    return result
# backend/controllers/user_controller.py

from fastapi import HTTPException
from datetime import datetime
from typing import List
from models.user import ProfileSummary, UserUpdateRequest, UserResponse
from config.database import get_collection

users_db = get_collection("collection_users")
groups_db = get_collection("collection_groups")
group_members_db = get_collection("collection_group_members")
tasks_db = get_collection("collection_tasks")
attachments_db = get_collection("collection_task_attachments")


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------

def iso_now() -> str:
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def default_summary():
    return {
        "total_tasks": 0,
        "completed_tasks": 0,
        "in_progress_tasks": 0,
        "pending_tasks": 0,
        "productivity_score": 0,
        "last_updated_summary": iso_now(),
    }


# ------------------------------------------------------------
# GET USER
# ------------------------------------------------------------

async def get_user(wallet_address: str) -> UserResponse:
    user = await users_db.find_one({"wallet_address": wallet_address})
    if not user:
        raise HTTPException(404, "User not found")

    summary, groups_info, all_tasks = await calculate_profile_summary(wallet_address)

    user["profile_summary"] = summary
    user["groups_overview"] = groups_info
    user["total_group_tasks"] = summary["total_tasks"]
    user["user_tasks"] = all_tasks

    return UserResponse(**user)


# ------------------------------------------------------------
# SUMMARY CALCULATION
# ------------------------------------------------------------

async def calculate_profile_summary(wallet_address: str):
    memberships = await group_members_db.find({"wallet_address": wallet_address}).to_list(None)
    if not memberships:
        return default_summary(), [], []

    groups_info = []
    all_tasks = []

    for member in memberships:
        group_id = member["group_id"]

        group = await groups_db.find_one({"group_id": group_id})
        if not group:
            continue

        group_tasks = await tasks_db.find({"group_id": group_id}).to_list(None)
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
            attachments = await attachments_db.find({"task_id": task_id}).to_list(None)
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
        "last_updated_summary": iso_now(),
    }

    return summary, groups_info, all_tasks


# ------------------------------------------------------------
# USER GROUP + TASK OVERVIEW
# ------------------------------------------------------------

async def get_user_groups_and_tasks(wallet_address: str):
    memberships = await group_members_db.find({"wallet_address": wallet_address}).to_list(None)

    if not memberships:
        return {"groups": [], "total_group_tasks": 0}

    groups_info = []
    total_tasks = 0

    for member in memberships:
        group_id = member["group_id"]

        group = await groups_db.find_one({"group_id": group_id})
        if not group:
            continue

        group_tasks = await tasks_db.find({"group_id": group_id}).to_list(None)
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


# ------------------------------------------------------------
# UPDATE USER
# ------------------------------------------------------------

async def update_user(wallet_address: str, updates: UserUpdateRequest) -> UserResponse:
    user = await users_db.find_one({"wallet_address": wallet_address})
    if not user:
        raise HTTPException(404, "User not found")

    update_data = updates.dict(exclude_unset=True)

    immutable_fields = {
        "wallet_address", "created_at", "profile_summary", "user_tasks",
        "proficiency_level", "last_used_at", "verified_by_tasks", "endorsed_by"
    }

    for field in immutable_fields:
        update_data.pop(field, None)

    # Merge preferences
    if "preferences" in update_data:
        current = user.get("preferences", {})
        current.update(update_data["preferences"])
        update_data["preferences"] = current

    # Mark update time
    if update_data:
        update_data["last_login"] = iso_now()

    # Update in DB
    updated = await users_db.find_one_and_update(
        {"wallet_address": wallet_address},
        {"$set": update_data},
        return_document=True
    )

    # Ensure summary exists
    if "profile_summary" not in updated:
        updated["profile_summary"] = default_summary()

    return UserResponse(**updated)


# ------------------------------------------------------------
# GET ALL USERS
# ------------------------------------------------------------

async def get_all_users() -> List[UserResponse]:
    users = await users_db.find({}).to_list(None)
    results = []

    for user in users:
        wallet_address = user.get("wallet_address")
        if not wallet_address:
            continue

        summary, groups_info, all_tasks = await calculate_profile_summary(wallet_address)

        user["profile_summary"] = summary
        user["groups_overview"] = groups_info
        user["total_group_tasks"] = summary["total_tasks"]
        user["user_tasks"] = all_tasks

        results.append(UserResponse(**user))

    return results

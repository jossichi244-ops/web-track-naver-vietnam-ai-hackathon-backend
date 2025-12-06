import uuid
from datetime import datetime
from fastapi import HTTPException, Request
from config.database import get_collection

tasks_db = get_collection("collection_tasks")
comments_db = get_collection("collection_task_comments")
group_members_db = get_collection("collection_group_members")
audit_logs_db = get_collection("collection_audit_logs")


def _format_datetime(dt: datetime) -> str:
    if dt.tzinfo is None:
        return dt.isoformat() + "Z"
    else:
        return dt.isoformat().replace("+00:00", "Z")


async def log_action(request: Request, user_id: str, wallet_address: str,
                     action: str, target_id: str | None = None):

    ip_address = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")

    log_doc = {
        "_id": uuid.uuid4().hex,
        "user_id": user_id,
        "wallet_address": wallet_address,
        "action": action,
        "target_id": target_id,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "created_at": _format_datetime(datetime.utcnow())
    }

    await audit_logs_db.insert_one(log_doc)


# =========================================
# 🔵 CREATE COMMENT
# =========================================

async def create_comment(data: dict, request: Request, user: dict):
    task = await tasks_db.find_one({"task_id": data.get("task_id")})
    if not task:
        raise HTTPException(404, "Task not found")

    # Nếu là group task
    if task.get("group_id"):
        member = await group_members_db.find_one({
            "wallet_address": user["wallet_address"],
            "group_id": task["group_id"]
        })
        if not member:
            raise HTTPException(403, "Not a member of this group")

    else:
        # Personal task → chỉ chính chủ mới được comment
        if task.get("user_id") != user["user_id"]:
            raise HTTPException(403, "Unauthorized")

    comment_id = f"cmt_{uuid.uuid4().hex}"
    now = _format_datetime(datetime.utcnow())

    comment = {
        "_id": comment_id,
        "task_id": task["task_id"],
        "user_id": user["user_id"],
        "wallet_address": user["wallet_address"],
        "content": data.get("content"),
        "replies_to_comment_id": data.get("replies_to_comment_id"),
        "created_at": now,
        "updated_at": now,
        "is_edited": False
    }

    await comments_db.insert_one(comment)
    await log_action(request, user["user_id"], user["wallet_address"], "create_comment", comment_id)

    return comment


# =========================================
# 🔵 LIST COMMENTS
# =========================================

async def list_comments(task_id: str):
    comments = await comments_db.find({"task_id": task_id}).to_list(None)
    return sorted(comments, key=lambda x: x["created_at"], reverse=True)


# =========================================
# 🔵 GET COMMENT
# =========================================

async def get_comment(comment_id: str):
    comment = await comments_db.find_one({"_id": comment_id})
    if not comment:
        raise HTTPException(404, "Comment not found")
    return comment


# =========================================
# 🔵 UPDATE COMMENT
# =========================================

async def update_comment(comment_id: str, updates: dict, request: Request, user: dict):
    comment = await comments_db.find_one({"_id": comment_id})
    if not comment:
        raise HTTPException(404, "Comment not found")

    if comment["user_id"] != user["user_id"]:
        raise HTTPException(403, "Only author can edit comment")

    new_data = {
        "content": updates.get("content", comment["content"]),
        "updated_at": _format_datetime(datetime.utcnow()),
        "is_edited": True,
    }

    await comments_db.update_one({"_id": comment_id}, {"$set": new_data})
    updated_comment = await comments_db.find_one({"_id": comment_id})

    await log_action(request, user["user_id"], user["wallet_address"], "update_comment", comment_id)

    return updated_comment


# =========================================
# 🔵 DELETE COMMENT
# =========================================

async def delete_comment(comment_id: str, request: Request, user: dict):
    comment = await comments_db.find_one({"_id": comment_id})
    if not comment:
        raise HTTPException(404, "Comment not found")

    task = await tasks_db.find_one({"task_id": comment["task_id"]})
    if not task:
        raise HTTPException(404, "Task not found")

    # Quyền xoá: chính chủ hoặc group owner
    can_delete = False

    if comment["user_id"] == user["user_id"]:
        can_delete = True

    elif task.get("group_id"):
        member = await group_members_db.find_one({
            "wallet_address": user["wallet_address"],
            "group_id": task["group_id"]
        })

        if member and member.get("role") == "owner":
            can_delete = True

    if not can_delete:
        raise HTTPException(403, "You don't have permission to delete this comment")

    await comments_db.delete_one({"_id": comment_id})

    await log_action(request, user["user_id"], user["wallet_address"], "delete_comment", comment_id)

    return {"status": "deleted", "comment_id": comment_id}

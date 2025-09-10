import uuid
from datetime import datetime
from fastapi import HTTPException, Request
from utils.jsondb import JsonDB

tasks_db = JsonDB("db/collection_tasks.json")
comments_db = JsonDB("db/collection_task_comments.json")
group_members_db = JsonDB("db/collection_group_members.json")
audit_logs_db = JsonDB("db/collection_audit_logs.json")


def _format_datetime(dt: datetime) -> str:
    if dt.tzinfo is None:
        return dt.isoformat() + "Z"
    else:
        return dt.isoformat().replace("+00:00", "Z")


def log_action(request: Request, user_id: str, wallet_address: str, action: str, target_id: str | None = None):
    ip_address = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")

    logs = audit_logs_db.read_all()
    logs.append({
        "_id": uuid.uuid4().hex,
        "user_id": user_id,
        "wallet_address": wallet_address,
        "action": action,
        "target_id": target_id,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "created_at": _format_datetime(datetime.utcnow())
    })
    audit_logs_db.write_all(logs)


def create_comment(data: dict, request: Request, user: dict):
    """Tạo comment trong task (chỉ member group hoặc chủ task cá nhân mới có quyền)."""
    task = tasks_db.find_one("task_id", data.get("task_id"))
    if not task:
        raise HTTPException(404, "Task not found")

    # Nếu là group task
    if task.get("group_id"):
        members = group_members_db.read_all()
        member = next(
            (m for m in members if m["wallet_address"] == user["wallet_address"] and m["group_id"] == task["group_id"]),
            None
        )
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

    comments_db.insert_or_replace("_id", comment_id, comment)
    log_action(request, user["user_id"], user["wallet_address"], "create_comment", comment_id)

    return comment


def list_comments(task_id: str):
    """Trả về danh sách comment theo task_id (mới nhất trước)."""
    comments = comments_db.read_all()
    return sorted([c for c in comments if c["task_id"] == task_id],
                  key=lambda x: x["created_at"], reverse=True)


def get_comment(comment_id: str):
    comment = comments_db.find_one("_id", comment_id)
    if not comment:
        raise HTTPException(404, "Comment not found")
    return comment


def update_comment(comment_id: str, updates: dict, request: Request, user: dict):
    comment = comments_db.find_one("_id", comment_id)
    if not comment:
        raise HTTPException(404, "Comment not found")

    if comment["user_id"] != user["user_id"]:
        raise HTTPException(403, "Only author can edit comment")

    comment.update({
        "content": updates.get("content", comment["content"]),
        "updated_at": _format_datetime(datetime.utcnow()),
        "is_edited": True
    })

    comments_db.insert_or_replace("_id", comment_id, comment)
    log_action(request, user["user_id"], user["wallet_address"], "update_comment", comment_id)

    return comment


def delete_comment(comment_id: str, request: Request, user: dict):
    comments = comments_db.read_all()
    comment = next((c for c in comments if c["_id"] == comment_id), None)
    if not comment:
        raise HTTPException(404, "Comment not found")

    task = tasks_db.find_one("task_id", comment["task_id"])
    if not task:
        raise HTTPException(404, "Task not found")

    # Quyền xoá: chính chủ hoặc group owner
    can_delete = False
    if comment["user_id"] == user["user_id"]:
        can_delete = True
    elif task.get("group_id"):
        members = group_members_db.read_all()
        member = next(
            (m for m in members if m["wallet_address"] == user["wallet_address"] and m["group_id"] == task["group_id"]),
            None
        )
        if member and member["role"] == "owner":
            can_delete = True

    if not can_delete:
        raise HTTPException(403, "You don't have permission to delete this comment")

    filtered = [c for c in comments if c["_id"] != comment_id]
    comments_db.write_all(filtered)

    log_action(request, user["user_id"], user["wallet_address"], "delete_comment", comment_id)

    return {"status": "deleted", "comment_id": comment_id}

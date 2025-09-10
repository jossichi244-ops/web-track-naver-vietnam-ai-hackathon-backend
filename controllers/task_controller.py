import uuid
from datetime import datetime
from fastapi import HTTPException, Request
from utils.jsondb import JsonDB
from models.task import TaskCreate, TaskUpdate

tasks_db = JsonDB("db/collection_tasks.json")
audit_logs_db = JsonDB("db/collection_audit_logs.json")
group_members_db = JsonDB("db/collection_group_members.json")
task_attachments_db = JsonDB("db/collection_task_attachments.json")
task_verifications_db = JsonDB("db/collection_task_verifications.json")


def _format_datetime(dt: datetime) -> str:
    if dt.tzinfo is None:
        return dt.isoformat() + "Z"
    else:
        return dt.isoformat().replace("+00:00", "Z")

def _calculate_fields(task: dict) -> dict:
    now = _format_datetime(datetime.utcnow())

    if "created_at" not in task:
        task["created_at"] = now
    task["updated_at"] = now

    if task.get("status") == "completed":
        task["is_completed"] = True
        task["completed_at"] = task.get("completed_at") or now
    else:
        task["is_completed"] = False
        task["completed_at"] = None

    priority = task.get("priority", "medium")
    task["color_code"] = {
        "high": "#ef4444",
        "medium": "#f59e0b",
        "low": "#10b981",
    }.get(priority, "#6b7280")

    return task

def create_task(data: TaskCreate, request: Request, user: dict):
    data_dict = data.dict(exclude_unset=True)
    
    if "status" not in data_dict:
        data_dict["status"] = "pending"
    
    if data_dict.get("due_date"):
        data_dict["due_date"] = _format_datetime(data_dict["due_date"])

    # Nếu là group task
    if data_dict.get("group_id"):
        # member = group_members_db.find_one("wallet_address", user["wallet_address"])
        members = group_members_db.read_all()
        member = next(
            (m for m in members if m["wallet_address"] == user["wallet_address"] and m["group_id"] == data_dict["group_id"]),
            None
        )
        if not member:
            raise HTTPException(403, "Not a member of this group")

        if member["role"] not in ["owner", "admin"]:
            raise HTTPException(403, "You don't have permission to create group tasks")
    else:
        # Nếu là cá nhân task → bắt buộc có user_id + wallet_address
        if not data_dict.get("user_id") or not data_dict.get("wallet_address"):
            raise HTTPException(400, "user_id and wallet_address required for personal tasks")

    task_id = f"task_{uuid.uuid4().hex}"
    task = {
        "_id": uuid.uuid4().hex,
        "task_id": task_id,
        **data_dict,
    }

    task = _calculate_fields(task)
    tasks_db.insert_or_replace("task_id", task_id, task)

    log_action(request, user["user_id"], user["wallet_address"], "create_task", task_id)

    return task


def get_task(task_id: str):
    task = tasks_db.find_one("task_id", task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


def list_tasks(wallet_address: str | None = None, user_id: str | None = None, group_id: str | None = None):
    tasks = tasks_db.read_all()
    if wallet_address:
        tasks = [t for t in tasks if t.get("wallet_address") == wallet_address]
    if user_id:
        tasks = [t for t in tasks if t.get("user_id") == user_id]
    if group_id:
        tasks = [t for t in tasks if t.get("group_id") == group_id]
    # Ensure status field present:
    for t in tasks:
        if "status" not in t:
            t["status"] = "pending"
    tasks = [_calculate_fields(t) for t in tasks]
    return tasks

def list_attachments(task_id: str, user: dict):
    # kiểm tra task có tồn tại không
    task = tasks_db.find_one("task_id", task_id)
    if not task:
        raise HTTPException(404, "Task not found")

    # Quyền xem: nếu là group thì user phải là thành viên
    if task.get("group_id"):
        members = group_members_db.read_all()
        member = next(
            (m for m in members if m["wallet_address"] == user["wallet_address"] and m["group_id"] == task["group_id"]),
            None
        )
        if not member:
            raise HTTPException(403, "Not a member of this group")

    else:
        # Task cá nhân thì chỉ chủ sở hữu được xem
        if task.get("user_id") != user["user_id"]:
            raise HTTPException(403, "Unauthorized")

    attachments = [a for a in task_attachments_db.read_all() if a["task_id"] == task_id]
    return attachments


def add_attachment(task_id: str, user: dict, file_name: str, file_url: str, file_size_bytes: int = 0, mime_type: str = ""):
    now = _format_datetime(datetime.utcnow())
    attachment = {
        "_id": f"attach_{uuid.uuid4().hex}",
        "task_id": task_id,
        "user_id": user["user_id"],
        "file_name": file_name,
        "file_url": file_url,
        "file_size_bytes": file_size_bytes,
        "mime_type": mime_type,
        "uploaded_at": now,
    }
    attachments = task_attachments_db.read_all()
    attachments.append(attachment)
    task_attachments_db.write_all(attachments)
    return attachment

def add_verification(task_id: str, user: dict, message: str, signature: str, tx_hash: str | None = None):
    now = _format_datetime(datetime.utcnow())
    verification = {
        "_id": f"verify_{uuid.uuid4().hex}",
        "task_id": task_id,
        "user_id": user["user_id"],
        "wallet_address": user["wallet_address"],
        "message": message,
        "signature": signature,
        "verified_on_chain": False,
        "tx_hash": tx_hash,
        "verified_at": now,
    }
    verifications = task_verifications_db.read_all()
    verifications.append(verification)
    task_verifications_db.write_all(verifications)
    return verification

def update_task(task_id: str, updates: TaskUpdate, request: Request, user: dict):
    updates_dict = updates.dict(exclude_unset=True)

    task = tasks_db.find_one("task_id", task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Quyền sửa
    if task.get("group_id"):
        members = group_members_db.read_all()
        member = next(
            (m for m in members if m["wallet_address"] == user["wallet_address"] and m["group_id"] == task["group_id"]),
            None
        )
        if not member:
            raise HTTPException(403, "Not a member of this group")

        if member["role"] not in ["owner", "admin"]:
            raise HTTPException(403, "You don't have permission to update group tasks")
    else:
        if task.get("user_id") != user["user_id"]:
            raise HTTPException(status_code=403, detail="Unauthorized")

    # Nếu cập nhật trạng thái thành completed → kiểm tra điều kiện
    if updates_dict.get("status") == "completed":
        attachments = [
            a for a in task_attachments_db.read_all()
            if a["task_id"] == task_id and a["user_id"] == user["user_id"]
        ]
        verifications = [
            v for v in task_verifications_db.read_all()
            if v["task_id"] == task_id and v["user_id"] == user["user_id"]
        ]
        if not attachments or not verifications:
            raise HTTPException(400, "Attachment and verification required to complete task")

    # ✅ Cập nhật bằng dict, không dùng updates.items()
    task.update(updates_dict)
    task = _calculate_fields(task)
    tasks_db.insert_or_replace("task_id", task_id, task)

    log_action(request, user["user_id"], user["wallet_address"], "update_task", task_id)
    return task

def delete_task(task_id: str, request: Request, user: dict):
    tasks = tasks_db.read_all()
    task = next((t for t in tasks if t["task_id"] == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Quyền xoá
    if task.get("group_id"):
        members = group_members_db.read_all()
        member = next(
            (m for m in members if m["wallet_address"] == user["wallet_address"] and m["group_id"] == task["group_id"]),
            None
        )
        if not member:
            raise HTTPException(403, "Not a member of this group")

        if member["role"] != "owner":
            raise HTTPException(403, "Only owner can delete group tasks")
    else:
        if task.get("user_id") != user["user_id"]:
            raise HTTPException(status_code=403, detail="Unauthorized")

    filtered = [t for t in tasks if t["task_id"] != task_id]
    tasks_db.write_all(filtered)

    log_action(request, user["user_id"], user["wallet_address"], "delete_task", task_id)

    return {"status": "deleted", "task_id": task_id}


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

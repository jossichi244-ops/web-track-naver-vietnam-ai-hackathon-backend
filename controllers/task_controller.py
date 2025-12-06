import uuid
from datetime import datetime
from fastapi import HTTPException, Request
from models.task import TaskCreate, TaskUpdate
from config.database import get_collection

tasks_db = get_collection("collection_tasks")
audit_logs_db = get_collection("collection_audit_logs")
group_members_db = get_collection("collection_group_members")
task_attachments_db = get_collection("collection_task_attachments")
task_verifications_db = get_collection("collection_task_verifications")
users_db = get_collection("collection_users")


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------

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


async def log_action(request: Request, user_id: str, wallet_address: str,
                     action: str, target_id: str | None = None):

    ip_address = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")

    await audit_logs_db.insert_one({
        "_id": uuid.uuid4().hex,
        "user_id": user_id,
        "wallet_address": wallet_address,
        "action": action,
        "target_id": target_id,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "created_at": _format_datetime(datetime.utcnow())
    })


# ------------------------------------------------------------
# CREATE TASK
# ------------------------------------------------------------

async def create_task(data: TaskCreate, request: Request, user: dict):
    data_dict = data.dict(exclude_unset=True)

    if "status" not in data_dict:
        data_dict["status"] = "pending"

    if data_dict.get("due_date"):
        data_dict["due_date"] = _format_datetime(data_dict["due_date"])

    # Group task
    if data_dict.get("group_id"):
        member = await group_members_db.find_one({
            "wallet_address": user["wallet_address"],
            "group_id": data_dict["group_id"]
        })

        if not member:
            raise HTTPException(403, "Not a member of this group")

        if member["role"] not in ["owner", "admin"]:
            raise HTTPException(403, "You don't have permission to create group tasks")

    else:
        if not data_dict.get("user_id") or not data_dict.get("wallet_address"):
            raise HTTPException(400, "user_id and wallet_address required for personal tasks")

    task_id = f"task_{uuid.uuid4().hex}"
    task = {
        "_id": uuid.uuid4().hex,
        "task_id": task_id,
        **data_dict,
    }

    task = _calculate_fields(task)

    await tasks_db.insert_one(task)
    await log_action(request, user["user_id"], user["wallet_address"], "create_task", task_id)

    return task


# ------------------------------------------------------------
# GET TASK
# ------------------------------------------------------------

async def get_task(task_id: str):
    task = await tasks_db.find_one({"task_id": task_id})
    if not task:
        raise HTTPException(404, "Task not found")
    return task


# ------------------------------------------------------------
# LIST TASKS
# ------------------------------------------------------------

async def list_tasks(wallet_address: str | None = None,
                     user_id: str | None = None,
                     group_id: str | None = None):

    query = {}
    if wallet_address:
        query["wallet_address"] = wallet_address
    if user_id:
        query["user_id"] = user_id
    if group_id:
        query["group_id"] = group_id

    tasks = await tasks_db.find(query).to_list(None)

    # Ensure status exists
    for t in tasks:
        if "status" not in t:
            t["status"] = "pending"

    return [_calculate_fields(t) for t in tasks]


# ------------------------------------------------------------
# LIST ATTACHMENTS
# ------------------------------------------------------------

async def list_attachments(task_id: str, user: dict):

    task = await tasks_db.find_one({"task_id": task_id})
    if not task:
        raise HTTPException(404, "Task not found")

    # Check permission
    if task.get("group_id"):
        member = await group_members_db.find_one({
            "wallet_address": user["wallet_address"],
            "group_id": task["group_id"]
        })
        if not member:
            raise HTTPException(403, "Not a member of this group")
    else:
        if task["user_id"] != user["user_id"]:
            raise HTTPException(403, "Unauthorized")

    attachments = await task_attachments_db.find({"task_id": task_id}).to_list(None)

    # Populate uploader info
    for a in attachments:
        uploader = await users_db.find_one({"_id": a.get("user_id")})
        a["user"] = uploader or None

    return attachments


# ------------------------------------------------------------
# ADD ATTACHMENT
# ------------------------------------------------------------

async def add_attachment(task_id: str, user: dict, file_name: str,
                         file_url: str, file_size_bytes: int = 0,
                         mime_type: str = ""):

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

    await task_attachments_db.insert_one(attachment)
    return attachment


# ------------------------------------------------------------
# ADD VERIFICATION
# ------------------------------------------------------------

async def add_verification(task_id: str, user: dict,
                           message: str, signature: str,
                           tx_hash: str | None = None):

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

    await task_verifications_db.insert_one(verification)
    return verification


# ------------------------------------------------------------
# UPDATE TASK
# ------------------------------------------------------------

async def update_task(task_id: str, updates: TaskUpdate,
                      request: Request, user: dict):

    task = await tasks_db.find_one({"task_id": task_id})
    if not task:
        raise HTTPException(404, "Task not found")

    # Permission
    if task.get("group_id"):
        member = await group_members_db.find_one({
            "wallet_address": user["wallet_address"],
            "group_id": task["group_id"]
        })

        if not member:
            raise HTTPException(403, "Not a member of this group")

        if member["role"] not in ["owner", "admin"]:
            raise HTTPException(403, "You don't have permission to update group tasks")
    else:
        if task["user_id"] != user["user_id"]:
            raise HTTPException(403, "Unauthorized")

    updates_dict = updates.dict(exclude_unset=True)

    # Validate completed
    if updates_dict.get("status") == "completed":
        attachments = await task_attachments_db.find({
            "task_id": task_id,
            "user_id": user["user_id"]
        }).to_list(None)

        verifications = await task_verifications_db.find({
            "task_id": task_id,
            "user_id": user["user_id"]
        }).to_list(None)

        if not attachments or not verifications:
            raise HTTPException(400, "Attachment and verification required to complete task")

    task.update(updates_dict)
    task = _calculate_fields(task)

    await tasks_db.update_one({"task_id": task_id}, {"$set": task})
    await log_action(request, user["user_id"], user["wallet_address"], "update_task", task_id)

    return task


# ------------------------------------------------------------
# DELETE TASK
# ------------------------------------------------------------

async def delete_task(task_id: str, request: Request, user: dict):
    task = await tasks_db.find_one({"task_id": task_id})
    if not task:
        raise HTTPException(404, "Task not found")

    # Permission
    if task.get("group_id"):
        member = await group_members_db.find_one({
            "wallet_address": user["wallet_address"],
            "group_id": task["group_id"]
        })

        if not member:
            raise HTTPException(403, "Not a member of this group")

        if member["role"] != "owner":
            raise HTTPException(403, "Only owner can delete group tasks")

    else:
        if task["user_id"] != user["user_id"]:
            raise HTTPException(403, "Unauthorized")

    await tasks_db.delete_one({"task_id": task_id})
    await log_action(request, user["user_id"], user["wallet_address"], "delete_task", task_id)

    return {"status": "deleted", "task_id": task_id}

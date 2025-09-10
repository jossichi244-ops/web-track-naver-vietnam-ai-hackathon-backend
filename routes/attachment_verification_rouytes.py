from fastapi import APIRouter, Depends, Request
from models.attachment_verification import TaskAttachmentCreate, TaskAttachmentResponse, TaskVerificationCreate, TaskVerificationResponse
from controllers import task_controller
from dependencies.auth import get_current_user 
from typing import List

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/{task_id}/attachments", response_model=TaskAttachmentResponse)
def upload_attachment(task_id: str, payload: TaskAttachmentCreate, request: Request, user: dict = Depends(get_current_user)):
    attachment = task_controller.add_attachment(
        task_id=task_id,
        user=user,
        file_name=payload.file_name,
        file_url=str(payload.file_url),
        file_size_bytes=payload.file_size_bytes or 0,
        mime_type=payload.mime_type or "",
    )
    return attachment


@router.post("/{task_id}/verifications", response_model=TaskVerificationResponse)
def verify_task(
    task_id: str,
    payload: TaskVerificationCreate,
    request: Request,
    user: dict = Depends(get_current_user),  
):
    verification = task_controller.add_verification(
        task_id=task_id,
        user=user,
        message=payload.message,
        signature=payload.signature,
        tx_hash=payload.tx_hash,
    )
    return verification

@router.get("/{task_id}/attachments", response_model=List[TaskAttachmentResponse])
def get_attachments(
    task_id: str,
    request: Request,
    user: dict = Depends(get_current_user)
):
    return task_controller.list_attachments(task_id, user)
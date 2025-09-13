from pydantic import BaseModel, Field, HttpUrl
from typing import Optional
from datetime import datetime


class TaskAttachmentCreate(BaseModel):
    file_name: str = Field(..., max_length=255)
    file_url: HttpUrl
    file_size_bytes: Optional[int] = Field(0, ge=0)
    mime_type: Optional[str] = None


class TaskAttachmentResponse(BaseModel):
    _id: str
    task_id: str
    user_id: str
    file_name: str
    file_url: HttpUrl
    file_size_bytes: int
    mime_type: Optional[str]
    uploaded_at: datetime
    user: Optional[dict]

class TaskVerificationCreate(BaseModel):
    message: str = Field(..., description="Message được ký: 'I completed task {task_id} at {timestamp}'")
    signature: str = Field(..., description="Chữ ký ECDSA từ ví")
    tx_hash: Optional[str] = None


class TaskVerificationResponse(BaseModel):
    _id: str
    task_id: str
    user_id: str
    wallet_address: str
    message: str
    signature: str
    verified_on_chain: bool
    tx_hash: Optional[str]
    verified_at: datetime

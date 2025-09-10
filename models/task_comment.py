from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class TaskCommentCreate(BaseModel):
    task_id: str
    content: str = Field(..., min_length=1, max_length=2000)
    replies_to_comment_id: Optional[str] = None


class TaskCommentUpdate(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)


class TaskCommentResponse(BaseModel):
    _id: str
    task_id: str
    user_id: str
    wallet_address: str
    content: str
    replies_to_comment_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    is_edited: bool

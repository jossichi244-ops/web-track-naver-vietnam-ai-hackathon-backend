from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Union
from datetime import datetime

class TaskMetadata(BaseModel):
    estimated_hours: Optional[float]
    actual_hours: Optional[float] = None         
    complexity_level: Optional[int] = Field(None, ge=1, le=5)
    required_skills: List[str]
    reviewer_wallet: Optional[str] = None        
    quality_rating: Optional[int] = Field(None, ge=1, le=5)
    feedback: Optional[str] = None                
    contribution_weight: Optional[float] = Field(None, ge=0, le=1)
    times_edited: Optional[int] = 0
    verification_rejected_count: Optional[int] = 0

class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    status: str = Field("pending", pattern="^(pending|in_progress|completed|archived)$")
    priority: str = Field("medium", pattern="^(low|medium|high)$")
    tags: List[str] = Field(..., min_items=1, max_items=5)
    due_date: Optional[datetime] = None
    metadata: Optional[TaskMetadata] = None

    # Cá nhân
    user_id: Optional[str] = None
    wallet_address: Optional[str] = None

    # Group
    group_id: Optional[str] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(pending|in_progress|completed|archived)$")
    priority: Optional[str] = Field(None, pattern="^(low|medium|high)$")
    tags: Optional[List[str]] = None
    due_date: Optional[datetime] = None
    metadata: Optional[Dict] = None


class TaskResponse(BaseModel):
    _id: str
    task_id: str
    title: str
    description: Optional[str] = None
    status: str
    priority: str
    tags: List[str]
    due_date: Optional[datetime]
    metadata: Optional[Union[TaskMetadata, Dict]] = None

    # Cá nhân
    user_id: Optional[str] = None
    wallet_address: Optional[str] = None

    # Group
    group_id: Optional[str] = None

    is_completed: bool
    color_code: str
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]

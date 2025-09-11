# backend/models/user.py
from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, Dict, List, Any
from datetime import datetime
from models.task import TaskResponse

class Preferences(BaseModel):
    theme: str = "light"
    notifications: bool = True
    web_push_enabled: bool = True
    language: str = "vi"

class ProfileSummary(BaseModel):
    total_tasks: int = 0
    completed_tasks: int = 0
    in_progress_tasks: int = 0
    pending_tasks: int = 0
    productivity_score: float = Field(0.0, ge=0.0, le=100.0)
    last_updated_summary: str  

class UserUpdateRequest(BaseModel):
    display_name: Optional[str] = Field(None, max_length=50)
    avatar_url: Optional[str] = None 
    preferences: Optional[Preferences] = None

    class Config:
        extra = "forbid"  

class UserResponse(BaseModel):
    _id: str
    wallet_address: str
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: str
    last_login: Optional[str] = None
    preferences: Optional[Preferences] = Preferences()
    profile_summary: ProfileSummary
    user_tasks: Optional[List[dict]] = []
    # Các field skill — giữ lại để tương thích AI/HR layer sau này
    skill_tag: Optional[str] = None
    proficiency_level: Optional[int] = Field(None, ge=1, le=5)
    last_used_at: Optional[str] = None
    verified_by_tasks: Optional[List[str]] = None
    endorsed_by: Optional[List[str]] = None
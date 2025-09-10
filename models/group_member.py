# models/group_member.py
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class GroupJoinRequest(BaseModel):
    group_id: str

class GroupMemberBase(BaseModel):
    group_id: str
    user_id: str
    wallet_address: str
    role: str = Field(default="member", pattern="^(owner|admin|member|guest)$")

class GroupMemberCreate(GroupMemberBase):
    pass

class GroupMemberUpdate(BaseModel):
    role: Optional[str] = Field(default=None, pattern="^(owner|admin|member|guest)$")
    # permissions: Optional[List[str]] = None
    wallet_address: str 
    # last_active_at: Optional[datetime] = None

class GroupMemberResponse(GroupMemberBase):
    _id: str
    joined_at: datetime
    # last_active_at: Optional[datetime]
    permissions: List[str]

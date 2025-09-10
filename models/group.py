# models/group.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class GroupBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    is_public: bool = Field(False)
    join_policy: str = Field("invite_only", pattern="^(invite_only|request_to_join|open)$")

class GroupCreate(GroupBase):
    pass  

class GroupUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    is_public: Optional[bool] = None
    join_policy: Optional[str] = Field(None, pattern="^(invite_only|request_to_join|open)$")

class GroupResponse(GroupBase):
    _id: str
    group_id: str
    wallet_address: str
    created_at: datetime
    updated_at: datetime
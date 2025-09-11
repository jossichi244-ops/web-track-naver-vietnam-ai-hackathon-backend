from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional
from datetime import datetime


class CommunityChallengeBase(BaseModel):
    challenge_url: HttpUrl
    title: Optional[str] = Field(None, max_length=150)
    description: Optional[str] = Field(None, max_length=500)
    tags: Optional[List[str]] = []


class CommunityChallengeCreate(CommunityChallengeBase):
    pass  # all required fields come from auth + auto `shared_at`


class CommunityChallengeInDB(CommunityChallengeBase):
    _id: str
    user_id: str
    wallet_address: str
    shared_at: datetime

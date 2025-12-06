from fastapi import APIRouter, Depends, HTTPException
from models.community_challenge import CommunityChallengeCreate, CommunityChallengeInDB
from dependencies.auth import get_current_user
from controllers.community_challenge_controller import (
    create_challenge,
    get_challenge,
    update_challenge,
    delete_challenge,
    list_challenges
)
from typing import List, Optional
from pydantic import HttpUrl

router = APIRouter(prefix="/community-challenges", tags=["Community Challenges"])


def share_challenge(challenge: CommunityChallengeCreate, current_user: dict):
    challenge_data = challenge.dict()

    for field, value in challenge_data.items():
        if isinstance(value, HttpUrl):
            challenge_data[field] = str(value)

    return create_challenge(
        challenge_data,
        current_user["user_id"],
        current_user["wallet_address"]
    )


@router.get("/{challenge_id}", response_model=CommunityChallengeInDB)
async def read_challenge(challenge_id: str):
    return await get_challenge(challenge_id)


@router.post("/", response_model=CommunityChallengeInDB)
async def create_new_challenge(
    challenge: CommunityChallengeCreate,
    current_user: dict = Depends(get_current_user)
):
    return await share_challenge(challenge, current_user)


@router.put("/{challenge_id}", response_model=CommunityChallengeInDB)
async def edit_challenge(
    challenge_id: str,
    updates: CommunityChallengeCreate,
    current_user: dict = Depends(get_current_user)
):
    return await update_challenge(
        challenge_id,
        updates.dict(),
        current_user["wallet_address"]
    )


@router.delete("/{challenge_id}")
async def remove_challenge(
    challenge_id: str,
    current_user: dict = Depends(get_current_user)
):
    return await delete_challenge(
        challenge_id,
        current_user["wallet_address"]
    )


@router.get("/", response_model=List[CommunityChallengeInDB])
async def list_all_challenges(
    wallet_address: Optional[str] = None,
    user_id: Optional[str] = None,
    tags: Optional[List[str]] = None
):
    challenges = await list_challenges(
        wallet_address=wallet_address,
        user_id=user_id,
        tags=tags
    )
    return challenges

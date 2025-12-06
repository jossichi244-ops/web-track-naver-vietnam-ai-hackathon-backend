from typing import List
from fastapi import APIRouter
from models.user import UserUpdateRequest, UserResponse
from controllers import user_controller

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/{wallet_address}", response_model=UserResponse)
async def get_user(wallet_address: str):
    return await user_controller.get_user(wallet_address)

@router.put("/{wallet_address}", response_model=UserResponse)
async def update_user(wallet_address: str, req: UserUpdateRequest):
    return await user_controller.update_user(wallet_address, req)

@router.patch("/{wallet_address}/preferences", response_model=UserResponse)
async def update_preferences(wallet_address: str, preferences: dict):
    req = UserUpdateRequest(preferences=preferences)
    return await user_controller.update_user(wallet_address, req)

@router.get("/", response_model=List[UserResponse])
async def get_all_users():
    return await user_controller.get_all_users()

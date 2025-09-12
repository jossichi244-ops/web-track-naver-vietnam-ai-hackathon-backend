# backend/routes/user_routes.py
from typing import List
from fastapi import APIRouter
from models.user import UserUpdateRequest, UserResponse
from controllers import user_controller


router = APIRouter(prefix="/users", tags=["users"])

@router.get("/{wallet_address}", response_model=UserResponse)
def get_user(wallet_address: str):
    return user_controller.get_user(wallet_address)

@router.put("/{wallet_address}", response_model=UserResponse)
def update_user(wallet_address: str, req: UserUpdateRequest): 
    return user_controller.update_user(wallet_address, req)   

@router.patch("/{wallet_address}/preferences", response_model=UserResponse)
def update_preferences(wallet_address: str, preferences: dict):
    # Tạo partial update request
    req = UserUpdateRequest(preferences=preferences)
    return user_controller.update_user(wallet_address, req)

@router.get("/", response_model=List[UserResponse])
def get_all_users():
    return user_controller.get_all_users()
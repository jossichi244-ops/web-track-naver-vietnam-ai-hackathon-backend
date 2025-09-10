# backend/routes/user_routes.py
from fastapi import APIRouter
from models.user import UserUpdateRequest, UserResponse
from controllers import user_controller

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/{wallet_address}", response_model=UserResponse)
def get_user(wallet_address: str):
    return user_controller.get_user(wallet_address)

@router.put("/{wallet_address}", response_model=UserResponse)
def update_user(wallet_address: str, req: UserUpdateRequest):  # <-- vẫn là model
    return user_controller.update_user(wallet_address, req)   # <-- truyền nguyên model, KHÔNG chuyển dict

@router.patch("/{wallet_address}/preferences", response_model=UserResponse)
def update_preferences(wallet_address: str, preferences: dict):
    # Tạo partial update request
    req = UserUpdateRequest(preferences=preferences)
    return user_controller.update_user(wallet_address, req)
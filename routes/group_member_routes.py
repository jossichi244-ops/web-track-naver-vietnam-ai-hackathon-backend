# routes/group_member_routes.py
from fastapi import APIRouter, Depends, status, Query
from typing import List
from models.group_member import (
    GroupJoinRequest,
    GroupMemberCreate,
    GroupMemberUpdate,
    GroupMemberResponse
)
from controllers import group_member_controller
from dependencies.auth import get_current_user

router = APIRouter(prefix="/group-members", tags=["group-members"])


@router.post("/", response_model=GroupMemberResponse, status_code=status.HTTP_201_CREATED)
async def add_member_route(req: GroupMemberCreate):
    """Owner/Admin thêm thành viên vào group"""
    return await group_member_controller.add_member(req.dict())


@router.post("/join", response_model=GroupMemberResponse, status_code=status.HTTP_201_CREATED)
async def join_group_route(group_id: str, current_user=Depends(get_current_user)):
    """Người dùng join group từ token"""
    return await group_member_controller.join_group({
        "group_id": group_id,
        "user_id": current_user["user_id"],
        "wallet_address": current_user["wallet_address"],
    })


@router.get("/{group_id}", response_model=List[GroupMemberResponse])
async def list_members_route(
    group_id: str,
    current_user=Depends(get_current_user)
):
    return await group_member_controller.get_members(group_id, current_user)


@router.patch("/by-wallet/{group_id}", response_model=GroupMemberResponse)
async def update_member_by_wallet_route(
    group_id: str,
    req: GroupMemberUpdate,
    wallet_address: str = Query(..., description="Wallet address of the member"),
):
    """Cập nhật role của member qua group_id + wallet_address"""
    return await group_member_controller.update_member_by_wallet(
        group_id,
        wallet_address,
        req.dict(exclude_unset=True)
    )


@router.delete("/{member_id}", status_code=status.HTTP_200_OK)
async def delete_member_route(member_id: str):
    return await group_member_controller.remove_member(member_id)

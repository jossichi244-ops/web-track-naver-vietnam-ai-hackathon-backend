# routes/group_routes.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from models.group import GroupCreate, GroupUpdate, GroupResponse
from controllers import group_controller
from dependencies.auth import get_current_user

router = APIRouter(prefix="/groups", tags=["groups"])


@router.post("/", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
def create_group_route(
    req: GroupCreate,
    current_user=Depends(get_current_user)
):
    """
    Tạo nhóm mới — tự động gán owner là người tạo
    """
    return group_controller.create_group(
        data=req.dict(),
        user_id=current_user["user_id"],
        wallet_address=current_user["wallet_address"]
    )

@router.get("/{group_id}", response_model=GroupResponse)
def get_group_route(group_id: str):
    """
    Lấy thông tin nhóm theo group_id
    (public: ai cũng xem được)
    """
    return group_controller.get_group(group_id)


@router.put("/{group_id}", response_model=GroupResponse)
def update_group_route(
    group_id: str,
    updates: GroupUpdate,
    user=Depends(get_current_user)
):
    """
    Cập nhật nhóm — chỉ owner mới có quyền
    """
    return group_controller.update_group(
        group_id,
        updates.dict(exclude_unset=True),
        user["wallet_address"]
    )


@router.delete("/{group_id}", status_code=status.HTTP_200_OK)
def delete_group_route(
    group_id: str,
    user=Depends(get_current_user)
):
    """
    Xóa nhóm — chỉ owner mới có quyền
    """
    return group_controller.delete_group(
        group_id,
        user["wallet_address"]
    )


@router.get("/", response_model=List[GroupResponse])
def list_groups_route(
    wallet_address: Optional[str] = None,
    wallet_addresses: Optional[List[str]] = Query(None),  # <-- thêm param
    is_public: Optional[bool] = None,
    user=Depends(get_current_user)
):
    """Liệt kê nhóm — có thể filter theo owner hoặc is_public"""

    if is_public:
        return group_controller.list_groups(None, True)

    if wallet_addresses:
        # Nếu có list wallet_addresses, lấy nhóm của các wallet này
        return group_controller.list_groups_multi(wallet_addresses, is_public)

    if wallet_address is None:
        wallet_address = user["wallet_address"]

    return group_controller.list_groups(wallet_address, is_public)
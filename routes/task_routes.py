from fastapi import APIRouter, Request, Depends
from models.task import TaskCreate, TaskResponse
from typing import List
from controllers import task_controller
from dependencies.auth import get_current_user

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.post("/", response_model=TaskResponse)
def create_task_route(req: TaskCreate, request: Request, user=Depends(get_current_user)):
        print("🟢 DEBUG create_task_route:")
        print(f"   user_id   = {user.get('user_id')}")
        print(f"   wallet_id = {user.get('wallet_address')}")
        print(f"   group_id  = {req.group_id if hasattr(req, 'group_id') else None}")
        return task_controller.create_task(req, request, user)

@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: str, user=Depends(get_current_user)):
    return task_controller.get_task(task_id)

@router.get("/", response_model=List[TaskResponse])
def list_tasks(
    wallet_address: str | None = None,
    user_id: str | None = None,
    group_id: str | None = None,
    user=Depends(get_current_user)
):
    raw_tasks = task_controller.list_tasks(wallet_address, user_id, group_id)
    # Parse to TaskResponse to ensure all fields are validated/present
    tasks = [TaskResponse(**t) for t in raw_tasks]
    return tasks

@router.put("/{task_id}", response_model=TaskResponse)
def update_task_route(task_id: str, updates: dict, request: Request, user=Depends(get_current_user)):
    return task_controller.update_task(task_id, updates, request, user)

@router.delete("/{task_id}")
def delete_task_route(task_id: str, request: Request, user=Depends(get_current_user)):
    return task_controller.delete_task(task_id, request, user)

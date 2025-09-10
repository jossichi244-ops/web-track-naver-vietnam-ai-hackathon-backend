from fastapi import APIRouter, Request, Depends
from typing import List
from models.task_comment import (
    TaskCommentCreate,
    TaskCommentUpdate,
    TaskCommentResponse,
)
from controllers import task_comment_controller
from dependencies.auth import get_current_user

router = APIRouter(prefix="/comments", tags=["comments"])


@router.post("/", response_model=TaskCommentResponse)
def create_comment_route(req: TaskCommentCreate, request: Request, user=Depends(get_current_user)):
    return task_comment_controller.create_comment(req.dict(), request, user)


@router.get("/task/{task_id}", response_model=List[TaskCommentResponse])
def list_comments_route(task_id: str, user=Depends(get_current_user)):
    return task_comment_controller.list_comments(task_id)


@router.get("/{comment_id}", response_model=TaskCommentResponse)
def get_comment_route(comment_id: str, user=Depends(get_current_user)):
    return task_comment_controller.get_comment(comment_id)


@router.put("/{comment_id}", response_model=TaskCommentResponse)
def update_comment_route(comment_id: str, req: TaskCommentUpdate, request: Request, user=Depends(get_current_user)):
    return task_comment_controller.update_comment(comment_id, req.dict(), request, user)


@router.delete("/{comment_id}")
def delete_comment_route(comment_id: str, request: Request, user=Depends(get_current_user)):
    return task_comment_controller.delete_comment(comment_id, request, user)

"""Task endpoints."""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select

from app.api.deps import SessionDep, CurrentUserDep, RequireAgent
from app.core.pagination import PaginationParams
from app.models.task import Task
from app.models.client import Client
from app.models.user import User
from app.schemas.task import TaskCreate, TaskRead, TaskUpdate
from app.services.task_service import TaskService

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=dict)
async def list_tasks(
    session: SessionDep,
    current_user: CurrentUserDep,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    client_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None),
    assignee_id: Optional[UUID] = Query(None),
):
    svc = TaskService(session, current_user)
    page_obj = await svc.list(
        PaginationParams(page=page, page_size=page_size),
        client_id=client_id,
        status=status,
        assignee_id=assignee_id,
    )
    return {
        "items": [TaskRead.model_validate(t) for t in page_obj.items],
        "total": page_obj.total,
        "page": page_obj.page,
        "page_size": page_obj.page_size,
        "total_pages": page_obj.total_pages,
        "has_next": page_obj.has_next,
        "has_previous": page_obj.has_previous,
    }


@router.post("", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
async def create_task(
    session: SessionDep,
    current_user: RequireAgent,
    data: TaskCreate,
):
    svc = TaskService(session, current_user)
    task = await svc.create(data)
    return TaskRead.model_validate(task)


@router.get("/{task_id}", response_model=TaskRead)
async def get_task(
    task_id: UUID,
    session: SessionDep,
    current_user: CurrentUserDep,
):
    svc = TaskService(session, current_user)
    task = await svc.get(task_id)
    return TaskRead.model_validate(task)


@router.patch("/{task_id}", response_model=TaskRead)
async def update_task(
    task_id: UUID,
    session: SessionDep,
    current_user: RequireAgent,
    data: TaskUpdate,
):
    svc = TaskService(session, current_user)
    task = await svc.update(task_id, data)
    return TaskRead.model_validate(task)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: UUID,
    session: SessionDep,
    current_user: RequireAgent,
):
    svc = TaskService(session, current_user)
    await svc.delete(task_id)
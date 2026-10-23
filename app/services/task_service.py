"""Task service — to-dos linked to clients or standalone."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import AuthorizationError, NotFoundError
from app.core.pagination import Page, PaginationParams
from app.models.task import Task
from app.models.client import Client
from app.models.user import User
from app.schemas.task import TaskCreate, TaskUpdate


class TaskService:
    def __init__(self, session: AsyncSession, actor: Optional[User] = None):
        self.session = session
        self.actor = actor

    async def list(
        self,
        params: PaginationParams,
        client_id: Optional[UUID] = None,
        status: Optional[str] = None,
        assignee_id: Optional[UUID] = None,
    ) -> Page[Task]:
        stmt = select(Task)
        if client_id:
            stmt = stmt.where(Task.client_id == client_id)
        if status:
            stmt = stmt.where(Task.status == status)
        if assignee_id:
            stmt = stmt.where(Task.assignee_id == assignee_id)

        total = (await self.session.execute(
            select(func.count()).select_from(stmt.subquery())
        )).scalar_one()
        stmt = (
            stmt.options(selectinload(Task.client), selectinload(Task.assignee))
            .order_by(Task.due_date.asc().nullslast(), Task.created_at.desc())
            .offset(params.offset)
            .limit(params.limit)
        )
        result = await self.session.execute(stmt)
        return Page.create(
            items=list(result.scalars().all()),
            total=total,
            page=params.page,
            page_size=params.page_size,
        )

    async def get(self, task_id: UUID) -> Task:
        result = await self.session.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()
        if task is None:
            raise NotFoundError("Task", task_id)
        return task

    async def create(self, data: TaskCreate) -> Task:
        if data.client_id:
            result = await self.session.execute(
                select(Client).where(Client.id == data.client_id)
            )
            if result.scalar_one_or_none() is None:
                raise NotFoundError("Client", data.client_id)
        task = Task(
            organization_id=None,
            client_id=data.client_id,
            assignee_id=data.assignee_id,
            title=data.title,
            description=data.description,
            status=data.status,
            priority=data.priority,
            due_date=data.due_date,
        )
        self.session.add(task)
        await self.session.commit()
        await self.session.refresh(task)
        return task

    async def update(self, task_id: UUID, data: TaskUpdate) -> Task:
        task = await self.get(task_id)
        changed = {}
        for field, value in data.model_dump(exclude_unset=True).items():
            if getattr(task, field) != value:
                changed[field] = value
            setattr(task, field, value)
        if "status" in changed and changed["status"] == "done":
            task.completed_at = datetime.now(timezone.utc)
        elif "status" in changed and changed["status"] != "done":
            task.completed_at = None
        await self.session.commit()
        await self.session.refresh(task)
        return task

    async def delete(self, task_id: UUID) -> None:
        task = await self.get(task_id)
        await self.session.delete(task)
        await self.session.commit()
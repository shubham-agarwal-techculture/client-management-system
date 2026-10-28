"""Task schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID


class TaskBase(BaseModel):
    client_id: Optional[UUID] = None
    title: str = Field(..., max_length=200)
    description: Optional[str] = None
    status: str = Field(default="todo", max_length=30)
    priority: str = Field(default="medium", max_length=20)
    due_date: Optional[datetime] = None
    assignee_id: Optional[UUID] = None


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    client_id: Optional[UUID] = None
    title: Optional[str] = Field(default=None, max_length=200)
    description: Optional[str] = None
    status: Optional[str] = Field(default=None, max_length=30)
    priority: Optional[str] = Field(default=None, max_length=20)
    due_date: Optional[datetime] = None
    assignee_id: Optional[UUID] = None


class TaskRead(TaskBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: Optional[UUID] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
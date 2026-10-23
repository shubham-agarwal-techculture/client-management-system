"""Interaction schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID


class InteractionBase(BaseModel):
    client_id: UUID
    interaction_type: str = Field(..., max_length=50)  # call | email | meeting | note ...
    direction: Optional[str] = Field(default=None, max_length=20)
    subject: Optional[str] = Field(default=None, max_length=200)
    body: Optional[str] = None
    occurred_at: Optional[datetime] = None


class InteractionCreate(InteractionBase):
    pass


class InteractionUpdate(BaseModel):
    interaction_type: Optional[str] = Field(default=None, max_length=50)
    direction: Optional[str] = Field(default=None, max_length=20)
    subject: Optional[str] = Field(default=None, max_length=200)
    body: Optional[str] = None
    occurred_at: Optional[datetime] = None


class InteractionRead(InteractionBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: Optional[UUID] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
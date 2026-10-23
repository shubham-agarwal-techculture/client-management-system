"""Tag schemas."""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID


class TagBase(BaseModel):
    name: str = Field(..., max_length=100)
    color: Optional[str] = Field(default=None, max_length=20)
    description: Optional[str] = None
    organization_id: Optional[UUID] = None


class TagCreate(TagBase):
    pass


class TagUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=100)
    color: Optional[str] = Field(default=None, max_length=20)
    description: Optional[str] = None


class TagRead(TagBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
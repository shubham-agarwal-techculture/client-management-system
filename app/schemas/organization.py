"""Organization schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID


class OrganizationBase(BaseModel):
    name: str = Field(..., max_length=200)
    slug: str = Field(..., max_length=100)
    is_active: bool = True


class OrganizationCreate(OrganizationBase):
    pass


class OrganizationUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=200)
    slug: Optional[str] = Field(default=None, max_length=100)
    is_active: Optional[bool] = None


class OrganizationRead(OrganizationBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
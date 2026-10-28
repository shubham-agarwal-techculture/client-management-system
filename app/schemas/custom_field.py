"""Custom field schemas."""

from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID


class CustomFieldBase(BaseModel):
    name: str = Field(..., max_length=150)
    field_type: str = Field(..., max_length=30)
    options: Optional[Any] = None
    required: bool = False
    is_active: bool = True
    organization_id: Optional[UUID] = None


class CustomFieldCreate(CustomFieldBase):
    pass


class CustomFieldUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=150)
    field_type: Optional[str] = Field(default=None, max_length=30)
    options: Optional[Any] = None
    required: Optional[bool] = None
    is_active: Optional[bool] = None


class CustomFieldRead(CustomFieldBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
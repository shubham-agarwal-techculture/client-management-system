"""Client schemas."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID


class ClientBase(BaseModel):
    name: str = Field(..., max_length=200)
    client_type: Optional[str] = Field(default=None, max_length=100)
    status: str = Field(default="active", max_length=50)
    email: Optional[str] = Field(default=None, max_length=255)
    phone: Optional[str] = Field(default=None, max_length=50)
    website: Optional[str] = Field(default=None, max_length=200)
    address: Optional[str] = None
    notes: Optional[str] = None
    owner_id: Optional[UUID] = None
    organization_id: Optional[UUID] = None


class ClientCreate(ClientBase):
    pass


class ClientUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=200)
    client_type: Optional[str] = Field(default=None, max_length=100)
    status: Optional[str] = Field(default=None, max_length=50)
    email: Optional[str] = Field(default=None, max_length=255)
    phone: Optional[str] = Field(default=None, max_length=50)
    website: Optional[str] = Field(default=None, max_length=200)
    address: Optional[str] = None
    notes: Optional[str] = None
    owner_id: Optional[UUID] = None
    organization_id: Optional[UUID] = None
    is_archived: Optional[bool] = None


class CustomValue(BaseModel):
    field_id: UUID
    value: Optional[str] = None


class ClientRead(ClientBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    is_archived: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    custom_values: Dict[str, Any] = {}
    tag_names: List[str] = []
"""User schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field
from uuid import UUID


class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = Field(default=None, max_length=200)
    role: str = Field(default="agent", max_length=50)
    is_active: bool = True
    organization_id: Optional[UUID] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=128)


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(default=None, max_length=200)
    role: Optional[str] = Field(default=None, max_length=50)
    is_active: Optional[bool] = None
    organization_id: Optional[UUID] = None
    password: Optional[str] = Field(default=None, min_length=6, max_length=128)


class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
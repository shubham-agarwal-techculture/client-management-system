"""Document schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID


class DocumentBase(BaseModel):
    filename: str = Field(..., max_length=300)
    client_id: Optional[UUID] = None


class DocumentRead(DocumentBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: Optional[UUID] = None
    storage_path: str
    mime_type: Optional[str] = None
    size_bytes: Optional[int] = None
    uploaded_by_id: Optional[UUID] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
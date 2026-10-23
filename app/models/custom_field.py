"""Custom field definitions — domain-agnostic extensibility.

Admins define fields (name + type) once; values live in ClientCustomValue.
This avoids schema migrations for every new client attribute.
"""

from typing import List, Optional
import uuid

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class CustomField(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "custom_fields"

    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    field_type: Mapped[str] = mapped_column(
        String(30), nullable=False
    )  # text | number | date | boolean | select
    options: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # JSON text of allowed values for select fields
    required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    values: Mapped[List["ClientCustomValue"]] = relationship(
        back_populates="field", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<CustomField {self.name}>"


# Bottom imports resolve string forward references in relationships.
from app.models.client_custom_value import ClientCustomValue  # noqa: E402
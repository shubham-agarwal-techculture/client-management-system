"""Custom field values attached to clients (EAV pattern)."""

from typing import Optional
import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDMixin


class ClientCustomValue(Base, UUIDMixin):
    __tablename__ = "client_custom_values"

    client_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    field_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("custom_fields.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Unique (client, field) pair is enforced via a DB constraint in migrations.
    client: Mapped["Client"] = relationship(back_populates="custom_values")
    field: Mapped["CustomField"] = relationship(back_populates="values")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<ClientCustomValue client={self.client_id} field={self.field_id}>"
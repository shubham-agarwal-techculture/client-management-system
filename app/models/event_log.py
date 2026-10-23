"""Audit / event log — records who did what, when, and on which entity."""

from datetime import datetime
from typing import Optional
import uuid

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class EventLog(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "event_logs"

    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("organizations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    actor_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    entity_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    event_metadata: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, name="metadata"
    )  # JSON text
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<EventLog {self.action} on {self.entity_type}>"
"""Task model — client-linked or standalone to-dos."""

from datetime import datetime
from typing import List, Optional
import uuid

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class Task(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "tasks"

    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    client_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    assignee_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    title: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="todo", index=True
    )  # todo | in_progress | done | cancelled
    priority: Mapped[str] = mapped_column(
        String(20), nullable=False, default="medium", index=True
    )  # low | medium | high | urgent
    due_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    client: Mapped[Optional["Client"]] = relationship(back_populates="tasks")
    assignee: Mapped[Optional["User"]] = relationship(
        back_populates="assigned_tasks", foreign_keys=[assignee_id]
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Task {self.title}>"
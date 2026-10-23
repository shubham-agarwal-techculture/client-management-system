"""Interaction model — a domain-agnostic communication log.

Supported types are open-ended (call, email, meeting, note, visit, other) so any
domain can record the interactions that matter to it.
"""

from datetime import datetime
from typing import List, Optional
import uuid

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class Interaction(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "interactions"

    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    client_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    interaction_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # call | email | meeting | note | visit | other
    direction: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True
    )  # inbound | outbound
    subject: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    occurred_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )

    client: Mapped["Client"] = relationship(back_populates="interactions")
    user: Mapped[Optional["User"]] = relationship(
        back_populates="interactions", foreign_keys=[user_id]
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Interaction {self.interaction_type} for client {self.client_id}>"
"""Organization model — the multi-tenancy boundary."""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class Organization(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    # Relationships (typing-only, populated by SQLAlchemy)
    users: Mapped[list["User"]] = relationship(
        back_populates="organization", cascade="all, delete-orphan"
    )
    clients: Mapped[list["Client"]] = relationship(
        back_populates="organization", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Organization {self.slug}>"
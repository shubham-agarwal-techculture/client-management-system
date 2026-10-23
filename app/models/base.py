"""Shared model mixins: primary keys, timestamps, soft deletes."""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Application declarative base.

    NOTE: `app.database.Base` re-exports this same object so there is a single
    metadata instance shared by the engine and the models.
    """

    pass


class UUIDMixin:
    """UUID primary key."""

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)


class TimestampMixin:
    """created_at / updated_at with automatic update on modification."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=True
    )


class SoftDeleteMixin:
    """Soft-delete support. Queries should filter `deleted_at IS NULL`."""

    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
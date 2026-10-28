"""Client model — the central entity of the system."""

from typing import List, Optional
import uuid

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin


class Client(Base, UUIDMixin, SoftDeleteMixin, TimestampMixin):
    __tablename__ = "clients"

    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("organizations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    owner_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    client_type: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, index=True
    )
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="active", index=True
    )
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    organization: Mapped[Optional["Organization"]] = relationship(
        back_populates="clients"
    )
    owner: Mapped[Optional["User"]] = relationship(
        back_populates="owned_clients", foreign_keys=[owner_id]
    )
    custom_values: Mapped[List["ClientCustomValue"]] = relationship(
        back_populates="client", cascade="all, delete-orphan"
    )
    tags: Mapped[List["Tag"]] = relationship(
        secondary="client_tags",
        back_populates="clients",
    )
    interactions: Mapped[List["Interaction"]] = relationship(
        back_populates="client", cascade="all, delete-orphan"
    )
    tasks: Mapped[List["Task"]] = relationship(
        back_populates="client", cascade="all, delete-orphan"
    )
    documents: Mapped[List["Document"]] = relationship(
        back_populates="client", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Client {self.name}>"


from app.models.organization import Organization  # noqa: E402
from app.models.user import User  # noqa: E402
from app.models.tag import Tag  # noqa: E402
from app.models.custom_field import CustomField  # noqa: E402
from app.models.client_custom_value import ClientCustomValue  # noqa: E402
from app.models.interaction import Interaction  # noqa: E402
from app.models.task import Task  # noqa: E402
from app.models.document import Document  # noqa: E402
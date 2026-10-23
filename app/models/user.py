"""User model with RBAC roles."""

import uuid
from typing import Optional

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin


class User(Base, UUIDMixin, SoftDeleteMixin, TimestampMixin):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    role: Mapped[str] = mapped_column(
        String(50), nullable=False, default="agent", index=True
    )  # admin | manager | agent | viewer
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("organizations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    organization: Mapped[Optional["Organization"]] = relationship(
        back_populates="users"
    )
    owned_clients: Mapped[list["Client"]] = relationship(
        back_populates="owner", foreign_keys="[Client.owner_id]"
    )
    assigned_tasks: Mapped[list["Task"]] = relationship(
        back_populates="assignee", foreign_keys="[Task.assignee_id]"
    )
    interactions: Mapped[list["Interaction"]] = relationship(
        back_populates="user", foreign_keys="[Interaction.user_id]"
    )
    uploaded_documents: Mapped[list["Document"]] = relationship(
        back_populates="uploaded_by", foreign_keys="[Document.uploaded_by_id]"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<User {self.email}>"

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    @property
    def is_manager(self) -> bool:
        return self.role in ("admin", "manager")


# Bottom imports resolve string forward references in relationships.
from app.models.organization import Organization  # noqa: E402
from app.models.task import Task  # noqa: E402
from app.models.interaction import Interaction  # noqa: E402
from app.models.document import Document  # noqa: E402
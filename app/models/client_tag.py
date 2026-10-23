"""Client <-> Tag many-to-many association."""

import uuid

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ClientTag(Base):
    __tablename__ = "client_tags"

    client_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("clients.id", ondelete="CASCADE"),
        primary_key=True,
    )
    tag_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tags.id", ondelete="CASCADE"),
        primary_key=True,
    )
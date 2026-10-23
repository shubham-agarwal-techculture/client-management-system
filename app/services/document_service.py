"""Document service — file metadata + pluggable storage."""

from __future__ import annotations

import uuid
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthorizationError, NotFoundError, StorageError
from app.core.pagination import Page, PaginationParams
from app.models.document import Document
from app.models.client import Client
from app.models.user import User
from app.schemas.document import DocumentRead
from app.services.storage import get_storage_backend


class DocumentService:
    def __init__(self, session: AsyncSession, actor: Optional[User] = None):
        self.session = session
        self.actor = actor

    async def list_for_client(
        self, client_id: UUID, params: PaginationParams
    ) -> Page[Document]:
        stmt = select(Document).where(Document.client_id == client_id)
        total = (await self.session.execute(
            select(func.count()).select_from(stmt.subquery())
        )).scalar_one()
        stmt = stmt.order_by(Document.created_at.desc()).offset(params.offset).limit(params.limit)
        result = await self.session.execute(stmt)
        return Page.create(
            items=list(result.scalars().all()),
            total=total,
            page=params.page,
            page_size=params.page_size,
        )

    async def get(self, document_id: UUID) -> Document:
        result = await self.session.execute(
            select(Document).where(Document.id == document_id)
        )
        doc = result.scalar_one_or_none()
        if doc is None:
            raise NotFoundError("Document", document_id)
        return doc

    async def upload(
        self,
        client_id: Optional[UUID],
        filename: str,
        file_data: bytes,
        content_type: Optional[str],
    ) -> Document:
        if client_id:
            result = await self.session.execute(
                select(Client).where(Client.id == client_id)
            )
            if result.scalar_one_or_none() is None:
                raise NotFoundError("Client", client_id)

        storage = get_storage_backend()
        try:
            storage_path = await storage.save(file_data, filename, content_type)
        except StorageError:
            raise

        doc = Document(
            organization_id=None,
            client_id=client_id,
            uploaded_by_id=self.actor.id if self.actor else None,
            filename=filename,
            storage_path=storage_path,
            mime_type=content_type,
            size_bytes=len(file_data),
        )
        self.session.add(doc)
        await self.session.commit()
        await self.session.refresh(doc)
        return doc

    async def delete(self, document_id: UUID) -> None:
        doc = await self.get(document_id)
        storage = get_storage_backend()
        try:
            await storage.delete(doc.storage_path)
        except StorageError:
            # continue so DB record can still be removed
            pass
        await self.session.delete(doc)
        await self.session.commit()

    async def download_path(self, document_id: UUID) -> tuple[str, str]:
        """Return (storage_path, filename) for serving the file."""
        doc = await self.get(document_id)
        return doc.storage_path, doc.filename
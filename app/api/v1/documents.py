"""Document endpoints — file attachments with pluggable storage."""

import os
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, status, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import func, select

from app.api.deps import SessionDep, CurrentUserDep, RequireAgent
from app.core.pagination import PaginationParams
from app.models.document import Document
from app.models.client import Client
from app.schemas.document import DocumentRead
from app.services.document_service import DocumentService

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("", response_model=dict)
async def list_documents(
    session: SessionDep,
    current_user: CurrentUserDep,
    client_id: Optional[UUID] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    stmt = select(Document)
    if client_id:
        stmt = stmt.where(Document.client_id == client_id)
    total = (
        await session.execute(select(func.count()).select_from(stmt.subquery()))
    ).scalar_one()
    stmt = (
        stmt.order_by(Document.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await session.execute(stmt)
    items = list(result.scalars().all())
    total_pages = max(1, (total + page_size - 1) // page_size)
    return {
        "items": [DocumentRead.model_validate(i) for i in items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_previous": page > 1,
    }


@router.post("", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
async def upload_document(
    session: SessionDep,
    current_user: RequireAgent,
    client_id: Optional[str] = None,
    file: UploadFile = File(...),
):
    cid = UUID(client_id) if client_id else None
    svc = DocumentService(session, current_user)
    data = await file.read()
    doc = await svc.upload(cid, file.filename or "upload", data, file.content_type)
    return DocumentRead.model_validate(doc)


@router.get("/{document_id}", response_model=DocumentRead)
async def get_document(
    document_id: UUID,
    session: SessionDep,
    current_user: CurrentUserDep,
):
    svc = DocumentService(session, current_user)
    doc = await svc.get(document_id)
    return DocumentRead.model_validate(doc)


@router.get("/download/{document_id}")
async def download_document(
    document_id: UUID,
    session: SessionDep,
    current_user: CurrentUserDep,
):
    svc = DocumentService(session, current_user)
    storage_path, filename = await svc.download_path(document_id)
    # Default local backend serves files from ./uploads/<storage_path>
    full = os.path.normpath(os.path.join("./uploads", storage_path))
    if not os.path.exists(full):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(full, filename=filename or os.path.basename(full))


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: UUID,
    session: SessionDep,
    current_user: RequireAgent,
):
    svc = DocumentService(session, current_user)
    await svc.delete(document_id)
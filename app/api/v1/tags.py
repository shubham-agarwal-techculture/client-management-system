"""Tag endpoints."""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from app.api.deps import SessionDep, CurrentUserDep, RequireManager
from app.core.exceptions import NotFoundError
from app.models.tag import Tag
from app.models.client_tag import ClientTag
from app.models.client import Client
from app.models.user import User
from app.schemas.tag import TagCreate, TagRead, TagUpdate

router = APIRouter(prefix="/tags", tags=["tags"])


@router.get("", response_model=List[TagRead])
async def list_tags(session: SessionDep, current_user: CurrentUserDep):
    result = await session.execute(select(Tag).order_by(Tag.name))
    return list(result.scalars().all())


@router.post("", response_model=TagRead, status_code=status.HTTP_201_CREATED)
async def create_tag(
    session: SessionDep,
    data: TagCreate,
    _: User = Depends(RequireManager),
):
    tag = Tag(
        name=data.name,
        color=data.color,
        description=data.description,
        organization_id=data.organization_id,
    )
    session.add(tag)
    await session.commit()
    await session.refresh(tag)
    return tag


@router.get("/{tag_id}/clients")
async def tag_clients(
    tag_id: UUID,
    session: SessionDep,
    current_user: CurrentUserDep,
    page: int = 1,
    page_size: int = 20,
):
    result = await session.execute(select(Tag).where(Tag.id == tag_id))
    tag = result.scalar_one_or_none()
    if not tag:
        raise NotFoundError("Tag", tag_id)
    result = await session.execute(
        select(ClientTag.client_id).where(ClientTag.tag_id == tag_id)
    )
    ids = [r[0] for r in result.all()]
    if not ids:
        return {"items": [], "total": 0, "page": page, "page_size": page_size,
                "total_pages": 0, "has_next": False, "has_previous": False}
    from app.api.v1.clients import _client_to_read
    result = await session.execute(select(Client).where(Client.id.in_(ids)))
    clients = list(result.scalars().all())
    return {
        "items": [_client_to_read(c) for c in clients],
        "total": len(clients),
        "page": page,
        "page_size": page_size,
        "total_pages": 1,
        "has_next": False,
        "has_previous": False,
    }


@router.patch("/{tag_id}", response_model=TagRead)
async def update_tag(
    tag_id: UUID,
    data: TagUpdate,
    session: SessionDep,
    _: User = Depends(RequireManager),
):
    result = await session.execute(select(Tag).where(Tag.id == tag_id))
    tag = result.scalar_one_or_none()
    if not tag:
        raise NotFoundError("Tag", tag_id)
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(tag, k, v)
    await session.commit()
    await session.refresh(tag)
    return tag


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(
    tag_id: UUID,
    session: SessionDep,
    _: User = Depends(RequireManager),
):
    result = await session.execute(select(Tag).where(Tag.id == tag_id))
    tag = result.scalar_one_or_none()
    if not tag:
        raise NotFoundError("Tag", tag_id)
    await session.delete(tag)
    await session.commit()
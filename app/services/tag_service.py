"""Tag service."""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import AuthorizationError, NotFoundError
from app.core.pagination import Page, PaginationParams
from app.models.tag import Tag
from app.models.client_tag import ClientTag
from app.models.client import Client
from app.models.user import User
from app.schemas.tag import TagCreate, TagUpdate


class TagService:
    def __init__(self, session: AsyncSession, actor: Optional[User] = None):
        self.session = session
        self.actor = actor

    async def list(
        self, params: PaginationParams, search: Optional[str] = None
    ) -> Page[Tag]:
        stmt = select(Tag)
        if search:
            like = f"%{search}%"
            stmt = stmt.where(Tag.name.ilike(like))
        total = (await self.session.execute(
            select(func.count()).select_from(stmt.subquery())
        )).scalar_one()
        stmt = stmt.order_by(Tag.name).offset(params.offset).limit(params.limit)
        result = await self.session.execute(stmt)
        return Page.create(
            items=list(result.scalars().all()),
            total=total,
            page=params.page,
            page_size=params.page_size,
        )

    async def get(self, tag_id: UUID) -> Tag:
        result = await self.session.execute(select(Tag).where(Tag.id == tag_id))
        tag = result.scalar_one_or_none()
        if tag is None:
            raise NotFoundError("Tag", tag_id)
        return tag

    async def create(self, data: TagCreate) -> Tag:
        tag = Tag(
            name=data.name,
            color=data.color,
            description=data.description,
            organization_id=data.organization_id,
        )
        self.session.add(tag)
        await self.session.commit()
        await self.session.refresh(tag)
        return tag

    async def update(self, tag_id: UUID, data: TagUpdate) -> Tag:
        tag = await self.get(tag_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(tag, field, value)
        await self.session.commit()
        await self.session.refresh(tag)
        return tag

    async def delete(self, tag_id: UUID) -> None:
        tag = await self.get(tag_id)
        await self.session.delete(tag)
        await self.session.commit()

    async def clients_for_tag(self, tag_id: UUID) -> List[Client]:
        await self.get(tag_id)  # ensure exists
        result = await self.session.execute(
            select(ClientTag.client_id).where(ClientTag.tag_id == tag_id)
        )
        ids = [row[0] for row in result.all()]
        if not ids:
            return []
        result = await self.session.execute(
            select(Client).where(Client.id.in_(ids))
        )
        return list(result.scalars().all())
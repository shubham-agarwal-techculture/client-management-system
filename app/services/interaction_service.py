"""Interaction service — communication log CRUD."""

from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import AuthorizationError, NotFoundError
from app.core.pagination import Page, PaginationParams
from app.models.interaction import Interaction
from app.models.client import Client
from app.models.user import User
from app.schemas.interaction import InteractionCreate, InteractionUpdate


class InteractionService:
    def __init__(self, session: AsyncSession, actor: Optional[User] = None):
        self.session = session
        self.actor = actor

    async def list_for_client(
        self,
        client_id: UUID,
        params: PaginationParams,
        interaction_type: Optional[str] = None,
    ) -> Page[Interaction]:
        # ensure client exists & access
        from app.services.client_service import ClientService

        client_svc = ClientService(self.session, self.actor)
        await client_svc.get(client_id, load_relations=False)

        stmt = select(Interaction).where(Interaction.client_id == client_id)
        if interaction_type:
            stmt = stmt.where(Interaction.interaction_type == interaction_type)

        total = (await self.session.execute(
            select(func.count()).select_from(stmt.subquery())
        )).scalar_one()
        stmt = (
            stmt.options(selectinload(Interaction.user))
            .order_by(Interaction.occurred_at.desc().nullslast(), Interaction.created_at.desc())
            .offset(params.offset)
            .limit(params.limit)
        )
        result = await self.session.execute(stmt)
        return Page.create(
            items=list(result.scalars().all()),
            total=total,
            page=params.page,
            page_size=params.page_size,
        )

    async def get(self, interaction_id: UUID) -> Interaction:
        result = await self.session.execute(
            select(Interaction).where(Interaction.id == interaction_id)
        )
        interaction = result.scalar_one_or_none()
        if interaction is None:
            raise NotFoundError("Interaction", interaction_id)
        return interaction

    async def create(self, data: InteractionCreate) -> Interaction:
        # verify client exists
        result = await self.session.execute(
            select(Client).where(Client.id == data.client_id)
        )
        if result.scalar_one_or_none() is None:
            raise NotFoundError("Client", data.client_id)

        interaction = Interaction(
            organization_id=None,  # set from client org if multi-tenant
            client_id=data.client_id,
            user_id=self.actor.id if self.actor else None,
            interaction_type=data.interaction_type,
            direction=data.direction,
            subject=data.subject,
            body=data.body,
            occurred_at=data.occurred_at,
        )
        self.session.add(interaction)
        await self.session.commit()
        await self.session.refresh(interaction)
        return interaction

    async def update(self, interaction_id: UUID, data: InteractionUpdate) -> Interaction:
        interaction = await self.get(interaction_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(interaction, field, value)
        await self.session.commit()
        await self.session.refresh(interaction)
        return interaction

    async def delete(self, interaction_id: UUID) -> None:
        interaction = await self.get(interaction_id)
        await self.session.delete(interaction)
        await self.session.commit()
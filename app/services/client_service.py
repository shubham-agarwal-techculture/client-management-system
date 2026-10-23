"""Client service — core CRUD with custom fields, tags, hooks, and audit logging."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.core.exceptions import (
    AlreadyExistsError,
    AuthorizationError,
    NotFoundError,
    ValidationError,
)
from app.core.pagination import Page, PaginationParams
from app.core.hooks import event_bus
from app.models.client import Client
from app.models.client_custom_value import ClientCustomValue
from app.models.custom_field import CustomField
from app.models.tag import Tag
from app.models.client_tag import ClientTag
from app.models.event_log import EventLog
from app.models.user import User
from app.schemas.client import ClientCreate, ClientUpdate, CustomValue


def _require_org_access(actor: Optional[User], org_id: Optional[UUID]) -> None:
    if not settings.multi_tenant:
        return
    if actor is None:
        return
    if actor.organization_id is not None and org_id is not None:
        if actor.organization_id != org_id and actor.role != "admin":
            raise AuthorizationError(
                "Cannot access clients outside your organization"
            )
    if settings.multi_tenant and org_id is None and actor.role != "admin":
        raise AuthorizationError("Organization context is required")


class ClientService:
    def __init__(self, session: AsyncSession, actor: Optional[User] = None):
        self.session = session
        self.actor = actor

    # ------------------------------------------------------------------ create
    async def create(
        self,
        data: ClientCreate,
        custom_values: List[CustomValue] = [],
        tag_names: List[str] = [],
    ) -> Client:
        org_id = data.organization_id
        _require_org_access(self.actor, org_id)

        await event_bus.emit(
            "client.before_create",
            data=data,
            actor=self.actor,
            organization_id=org_id,
        )

        client = Client(
            organization_id=org_id,
            owner_id=data.owner_id,
            name=data.name,
            client_type=data.client_type,
            status=data.status,
            email=data.email,
            phone=data.phone,
            website=data.website,
            address=data.address,
            notes=data.notes,
        )
        self.session.add(client)
        await self.session.flush()

        await self._set_custom_values(client, custom_values)
        await self._set_tags(client, tag_names)

        await self._log_event(
            "client.created",
            entity_type="client",
            entity_id=str(client.id),
            metadata={"name": client.name, "status": client.status},
        )

        await event_bus.emit(
            "client.after_create",
            client=client,
            actor=self.actor,
        )
        await self.session.commit()
        await self.session.refresh(client)
        return client

    # ------------------------------------------------------------------ read
    async def get(self, client_id: UUID, load_relations: bool = True) -> Client:
        stmt = select(Client).where(Client.id == client_id)
        if load_relations:
            stmt = stmt.options(
                selectinload(Client.custom_values).selectinload(
                    ClientCustomValue.field
                ),
                selectinload(Client.tags),
            )
        result = await self.session.execute(stmt)
        client = result.scalar_one_or_none()
        if client is None or client.deleted_at is not None:
            raise NotFoundError("Client", client_id)
        _require_org_access(self.actor, client.organization_id)
        return client

    # ------------------------------------------------------------------ list
    async def list(
        self,
        params: PaginationParams,
        search: Optional[str] = None,
        client_type: Optional[str] = None,
        status: Optional[str] = None,
        owner_id: Optional[UUID] = None,
        tag: Optional[str] = None,
        archived: bool = False,
    ) -> Page[Client]:
        _require_org_access(self.actor, None)

        stmt = select(Client).where(Client.is_archived == archived)
        if settings.multi_tenant and self.actor and self.actor.organization_id:
            if self.actor.role != "admin":
                stmt = stmt.where(
                    (Client.organization_id == self.actor.organization_id)
                    | (Client.organization_id.is_(None))
                )

        if search:
            like = f"%{search}%"
            stmt = stmt.where(
                or_(
                    Client.name.ilike(like),
                    Client.email.ilike(like),
                    Client.phone.ilike(like),
                )
            )
        if client_type:
            stmt = stmt.where(Client.client_type == client_type)
        if status:
            stmt = stmt.where(Client.status == status)
        if owner_id:
            stmt = stmt.where(Client.owner_id == owner_id)
        if tag:
            stmt = stmt.join(Client.tags).where(Tag.name == tag)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.session.execute(count_stmt)).scalar_one()

        stmt = (
            stmt.options(selectinload(Client.tags))
            .order_by(Client.created_at.desc())
            .offset(params.offset)
            .limit(params.limit)
        )
        result = await self.session.execute(stmt)
        items = result.scalars().all()

        return Page.create(
            items=list(items),
            total=total,
            page=params.page,
            page_size=params.page_size,
        )

    # ------------------------------------------------------------------ update
    async def update(
        self,
        client_id: UUID,
        data: ClientUpdate,
        custom_values: Optional[List[CustomValue]] = None,
        tag_names: Optional[List[str]] = None,
    ) -> Client:
        client = await self.get(client_id, load_relations=False)
        _require_org_access(self.actor, client.organization_id)

        await event_bus.emit(
            "client.before_update",
            client=client,
            data=data,
            actor=self.actor,
        )

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(client, field, value)

        self.session.add(client)
        await self.session.flush()

        if custom_values is not None:
            await self._set_custom_values(client, custom_values)
        if tag_names is not None:
            await self._set_tags(client, tag_names)

        await self._log_event(
            "client.updated",
            entity_type="client",
            entity_id=str(client.id),
            metadata={"updated_fields": list(update_data.keys())},
        )

        await event_bus.emit(
            "client.after_update",
            client=client,
            actor=self.actor,
        )
        await self.session.commit()
        await self.session.refresh(client)
        return client

    # ------------------------------------------------------------------ delete
    async def delete(self, client_id: UUID, hard: bool = False) -> None:
        client = await self.get(client_id, load_relations=False)
        _require_org_access(self.actor, client.organization_id)

        await event_bus.emit(
            "client.before_delete",
            client=client,
            actor=self.actor,
        )

        if hard:
            await self.session.delete(client)
        else:
            client.deleted_at = datetime.now(timezone.utc)
            client.is_archived = True
            self.session.add(client)

        await self._log_event(
            "client.deleted",
            entity_type="client",
            entity_id=str(client.id),
            metadata={"name": client.name, "hard": hard},
        )

        await event_bus.emit(
            "client.after_delete",
            client=client,
            actor=self.actor,
        )
        await self.session.commit()

    # ------------------------------------------------------------------ internals
    async def _set_custom_values(
        self, client: Client, values: List[CustomValue]
    ) -> None:
        await self.session.execute(
            ClientCustomValue.__table__.delete().where(
                ClientCustomValue.client_id == client.id
            )
        )
        for cv in values:
            result = await self.session.execute(
                select(CustomField).where(CustomField.id == cv.field_id)
            )
            field = result.scalar_one_or_none()
            if field is None:
                raise NotFoundError("CustomField", cv.field_id)
            if (
                settings.multi_tenant
                and field.organization_id is not None
                and client.organization_id is not None
                and field.organization_id != client.organization_id
            ):
                raise AuthorizationError(
                    "Custom field belongs to a different organization"
                )
            self.session.add(
                ClientCustomValue(
                    client_id=client.id,
                    field_id=cv.field_id,
                    value=cv.value,
                )
            )

    async def _set_tags(self, client: Client, tag_names: List[str]) -> None:
        await self.session.execute(
            ClientTag.__table__.delete().where(ClientTag.client_id == client.id)
        )
        for name in tag_names:
            name = name.strip()
            if not name:
                continue
            result = await self.session.execute(
                select(Tag).where(Tag.name == name)
            )
            tag = result.scalar_one_or_none()
            if tag is None:
                tag = Tag(name=name, organization_id=client.organization_id)
                self.session.add(tag)
                await self.session.flush()
            self.session.add(ClientTag(client_id=client.id, tag_id=tag.id))

    async def _log_event(
        self,
        action: str,
        entity_type: str,
        entity_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        import json

        self.session.add(
            EventLog(
                organization_id=self.actor.organization_id if self.actor else None,
                actor_user_id=self.actor.id if self.actor else None,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                event_metadata=json.dumps(metadata or {}),
                occurred_at=datetime.now(timezone.utc),
            )
        )
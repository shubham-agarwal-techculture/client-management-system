"""Interaction (communication log) endpoints."""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select

from app.api.deps import SessionDep, CurrentUserDep, RequireAgent
from app.core.pagination import PaginationParams
from app.models.interaction import Interaction
from app.models.client import Client
from app.models.user import User
from app.schemas.interaction import InteractionCreate, InteractionRead, InteractionUpdate
from app.services.interaction_service import InteractionService

router = APIRouter(prefix="/interactions", tags=["interactions"])


@router.get("/clients/{client_id}", response_model=dict)
async def list_interactions(
    client_id: UUID,
    session: SessionDep,
    current_user: CurrentUserDep,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    interaction_type: Optional[str] = Query(None),
):
    from app.services.client_service import ClientService

    ClientService(session, current_user).get(client_id, load_relations=False)
    svc = InteractionService(session, current_user)
    page_obj = await svc.list_for_client(
        client_id,
        PaginationParams(page=page, page_size=page_size),
        interaction_type=interaction_type,
    )
    return {
        "items": [InteractionRead.model_validate(i) for i in page_obj.items],
        "total": page_obj.total,
        "page": page_obj.page,
        "page_size": page_obj.page_size,
        "total_pages": page_obj.total_pages,
        "has_next": page_obj.has_next,
        "has_previous": page_obj.has_previous,
    }


@router.post("", response_model=InteractionRead, status_code=status.HTTP_201_CREATED)
async def create_interaction(
    session: SessionDep,
    current_user: RequireAgent,
    data: InteractionCreate,
):
    svc = InteractionService(session, current_user)
    interaction = await svc.create(data)
    return InteractionRead.model_validate(interaction)


@router.get("/{interaction_id}", response_model=InteractionRead)
async def get_interaction(
    interaction_id: UUID,
    session: SessionDep,
    current_user: CurrentUserDep,
):
    svc = InteractionService(session, current_user)
    interaction = await svc.get(interaction_id)
    return InteractionRead.model_validate(interaction)


@router.patch("/{interaction_id}", response_model=InteractionRead)
async def update_interaction(
    interaction_id: UUID,
    session: SessionDep,
    current_user: RequireAgent,
    data: InteractionUpdate,
):
    svc = InteractionService(session, current_user)
    interaction = await svc.update(interaction_id, data)
    return InteractionRead.model_validate(interaction)


@router.delete("/{interaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_interaction(
    interaction_id: UUID,
    session: SessionDep,
    current_user: RequireAgent,
):
    svc = InteractionService(session, current_user)
    await svc.delete(interaction_id)
"""Client endpoints — the central resource of the CMS."""

from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select

from app.api.deps import SessionDep, CurrentUserDep, RequireAgent, RequireManager
from app.core.pagination import PaginationParams
from app.models.client import Client
from app.models.client_custom_value import ClientCustomValue
from app.models.custom_field import CustomField
from app.models.tag import Tag
from app.schemas.client import ClientCreate, ClientRead, ClientUpdate, CustomValue
from app.services.client_service import ClientService

router = APIRouter(prefix="/clients", tags=["clients"])


def _client_to_read(client: Client) -> ClientRead:
    custom_values: Dict[str, Any] = {}
    for cv in client.custom_values or []:
        field = cv.field
        custom_values[field.name if field else str(cv.field_id)] = cv.value
    return ClientRead(
        id=client.id,
        organization_id=client.organization_id,
        owner_id=client.owner_id,
        name=client.name,
        client_type=client.client_type,
        status=client.status,
        email=client.email,
        phone=client.phone,
        website=client.website,
        address=client.address,
        notes=client.notes,
        is_archived=client.is_archived,
        created_at=client.created_at,
        updated_at=client.updated_at,
        custom_values=custom_values,
        tag_names=[t.name for t in (client.tags or [])],
    )


@router.get("", response_model=Dict[str, Any])
async def list_clients(
    session: SessionDep,
    current_user: CurrentUserDep,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    client_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    owner_id: Optional[UUID] = Query(None),
    tag: Optional[str] = Query(None),
    archived: bool = Query(False),
):
    svc = ClientService(session, current_user)
    page_obj = await svc.list(
        PaginationParams(page=page, page_size=page_size),
        search=search,
        client_type=client_type,
        status=status,
        owner_id=owner_id,
        tag=tag,
        archived=archived,
    )
    return {
        "items": [_client_to_read(c) for c in page_obj.items],
        "total": page_obj.total,
        "page": page_obj.page,
        "page_size": page_obj.page_size,
        "total_pages": page_obj.total_pages,
        "has_next": page_obj.has_next,
        "has_previous": page_obj.has_previous,
    }


@router.post("", response_model=ClientRead, status_code=status.HTTP_201_CREATED)
async def create_client(
    session: SessionDep,
    current_user: RequireAgent,
    data: ClientCreate,
    custom_values: List[CustomValue] = [],
    tag_names: List[str] = [],
):
    svc = ClientService(session, current_user)
    client = await svc.create(data, custom_values=custom_values, tag_names=tag_names)
    # reload with relations for the response
    client = await svc.get(client.id, load_relations=True)
    return _client_to_read(client)


@router.get("/{client_id}", response_model=ClientRead)
async def get_client(
    client_id: UUID,
    session: SessionDep,
    current_user: CurrentUserDep,
):
    svc = ClientService(session, current_user)
    client = await svc.get(client_id, load_relations=True)
    return _client_to_read(client)


@router.patch("/{client_id}", response_model=ClientRead)
async def update_client(
    client_id: UUID,
    session: SessionDep,
    current_user: RequireAgent,
    data: ClientUpdate,
    custom_values: Optional[List[CustomValue]] = None,
    tag_names: Optional[List[str]] = None,
):
    svc = ClientService(session, current_user)
    client = await svc.update(
        client_id, data, custom_values=custom_values, tag_names=tag_names
    )
    client = await svc.get(client.id, load_relations=True)
    return _client_to_read(client)


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_client(
    client_id: UUID,
    session: SessionDep,
    current_user: RequireManager,
    hard: bool = Query(False),
):
    svc = ClientService(session, current_user)
    await svc.delete(client_id, hard=hard)
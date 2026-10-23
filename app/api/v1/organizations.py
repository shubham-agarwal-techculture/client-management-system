"""Organization endpoints."""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from app.api.deps import SessionDep, CurrentUserDep
from app.dependencies import require_roles
from app.models.organization import Organization
from app.models.user import User
from app.schemas.organization import OrganizationRead, OrganizationCreate, OrganizationUpdate

router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.get("", response_model=List[OrganizationRead])
async def list_orgs(
    session: SessionDep, _: User = Depends(require_roles("admin"))
):
    result = await session.execute(select(Organization).order_by(Organization.name))
    return list(result.scalars().all())


@router.post(
    "", response_model=OrganizationRead, status_code=status.HTTP_201_CREATED
)
async def create_org(
    session: SessionDep,
    data: OrganizationCreate,
    _: User = Depends(require_roles("admin")),
):
    result = await session.execute(
        select(Organization).where(Organization.slug == data.slug)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Slug already exists"
        )
    org = Organization(name=data.name, slug=data.slug, is_active=data.is_active)
    session.add(org)
    await session.commit()
    await session.refresh(org)
    return org


@router.get("/{org_id}", response_model=OrganizationRead)
async def get_org(
    org_id: UUID,
    session: SessionDep,
    current_user: CurrentUserDep,
    _: User = Depends(require_roles("admin")),
):
    result = await session.execute(select(Organization).where(Organization.id == org_id))
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return org


@router.patch("/{org_id}", response_model=OrganizationRead)
async def update_org(
    org_id: UUID,
    data: OrganizationUpdate,
    session: SessionDep,
    _: User = Depends(require_roles("admin")),
):
    result = await session.execute(select(Organization).where(Organization.id == org_id))
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(org, field, value)
    await session.commit()
    await session.refresh(org)
    return org
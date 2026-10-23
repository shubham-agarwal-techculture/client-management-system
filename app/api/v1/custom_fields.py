"""Custom field definition endpoints — domain-agnostic extensibility."""

from typing import Any, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from app.api.deps import SessionDep, CurrentUserDep, RequireManager
from app.core.exceptions import NotFoundError
from app.models.custom_field import CustomField
from app.models.user import User
from app.schemas.custom_field import (
    CustomFieldCreate,
    CustomFieldRead,
    CustomFieldUpdate,
)

router = APIRouter(prefix="/custom-fields", tags=["custom-fields"])


def _to_read(field: CustomField) -> CustomFieldRead:
    import json

    options = None
    if field.options:
        try:
            options = json.loads(field.options)
        except Exception:
            options = field.options
    return CustomFieldRead(
        id=field.id,
        organization_id=field.organization_id,
        name=field.name,
        field_type=field.field_type,
        options=options,
        required=field.required,
        is_active=field.is_active,
        created_at=str(field.created_at) if field.created_at else None,
        updated_at=str(field.updated_at) if field.updated_at else None,
    )


@router.get("", response_model=List[CustomFieldRead])
async def list_custom_fields(
    session: SessionDep,
    current_user: CurrentUserDep,
    organization_id: Optional[UUID] = None,
):
    stmt = select(CustomField).where(CustomField.is_active == True)  # noqa: E712
    if organization_id:
        stmt = stmt.where(CustomField.organization_id == organization_id)
    result = await session.execute(stmt.order_by(CustomField.name))
    return [_to_read(f) for f in result.scalars().all()]


@router.post(
    "", response_model=CustomFieldRead, status_code=status.HTTP_201_CREATED
)
async def create_custom_field(
    session: SessionDep,
    data: CustomFieldCreate,
    _: User = Depends(RequireManager),
):
    import json

    field = CustomField(
        organization_id=data.organization_id,
        name=data.name,
        field_type=data.field_type,
        options=json.dumps(data.options) if data.options is not None else None,
        required=data.required,
        is_active=data.is_active,
    )
    session.add(field)
    await session.commit()
    await session.refresh(field)
    return _to_read(field)


@router.patch("/{field_id}", response_model=CustomFieldRead)
async def update_custom_field(
    field_id: UUID,
    data: CustomFieldUpdate,
    session: SessionDep,
    _: User = Depends(RequireManager),
):
    import json

    result = await session.execute(select(CustomField).where(CustomField.id == field_id))
    field = result.scalar_one_or_none()
    if not field:
        raise NotFoundError("CustomField", field_id)
    payload = data.model_dump(exclude_unset=True)
    if "options" in payload:
        payload["options"] = (
            json.dumps(payload["options"]) if payload["options"] is not None else None
        )
    for k, v in payload.items():
        setattr(field, k, v)
    await session.commit()
    await session.refresh(field)
    return _to_read(field)


@router.delete("/{field_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_custom_field(
    field_id: UUID,
    session: SessionDep,
    _: User = Depends(RequireManager),
):
    result = await session.execute(select(CustomField).where(CustomField.id == field_id))
    field = result.scalar_one_or_none()
    if not field:
        raise NotFoundError("CustomField", field_id)
    await session.delete(field)
    await session.commit()
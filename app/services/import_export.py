"""Import/export helpers for clients (CSV / JSON). Uses only the standard library."""

import csv
import io
import json
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.client import Client
from app.models.client_custom_value import ClientCustomValue
from app.models.custom_field import CustomField
from app.models.tag import Tag
from app.models.client_tag import ClientTag
from app.core.exceptions import NotFoundError


CLIENT_CSV_FIELDS = [
    "name",
    "client_type",
    "status",
    "email",
    "phone",
    "website",
    "address",
    "notes",
    "owner_id",
    "organization_id",
]


async def export_clients_json(session: AsyncSession, client_ids: List[UUID]) -> str:
    rows: List[Dict[str, Any]] = []
    for cid in client_ids:
        result = await session.execute(select(Client).where(Client.id == cid))
        client = result.scalar_one_or_none()
        if client is None:
            raise NotFoundError("Client", cid)
        rows.append(
            {
                "id": str(client.id),
                "name": client.name,
                "client_type": client.client_type,
                "status": client.status,
                "email": client.email,
                "phone": client.phone,
                "website": client.website,
                "address": client.address,
                "notes": client.notes,
                "owner_id": str(client.owner_id) if client.owner_id else None,
                "organization_id": (
                    str(client.organization_id) if client.organization_id else None
                ),
                "custom_values": {
                    str(cv.field_id): cv.value for cv in client.custom_values
                },
                "tags": [t.name for t in client.tags],
            }
        )
    return json.dumps(rows, indent=2, default=str)


async def export_clients_csv(session: AsyncSession, client_ids: List[UUID]) -> str:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=CLIENT_CSV_FIELDS, extrasaction="ignore")
    writer.writeheader()
    for cid in client_ids:
        result = await session.execute(select(Client).where(Client.id == cid))
        client = result.scalar_one_or_none()
        if client is None:
            raise NotFoundError("Client", cid)
        writer.writerow(
            {
                "name": client.name,
                "client_type": client.client_type or "",
                "status": client.status,
                "email": client.email or "",
                "phone": client.phone or "",
                "website": client.website or "",
                "address": client.address or "",
                "notes": client.notes or "",
                "owner_id": str(client.owner_id) if client.owner_id else "",
                "organization_id": (
                    str(client.organization_id) if client.organization_id else ""
                ),
            }
        )
    return output.getvalue()


async def import_clients_json(
    session: AsyncSession, payload: str, actor_org_id: Optional[UUID] = None
) -> List[Client]:
    data = json.loads(payload)
    if not isinstance(data, list):
        raise ValueError("JSON import must be a list of client objects")
    created: List[Client] = []
    for item in data:
        client = Client(
            name=item["name"],
            client_type=item.get("client_type"),
            status=item.get("status", "active"),
            email=item.get("email"),
            phone=item.get("phone"),
            website=item.get("website"),
            address=item.get("address"),
            notes=item.get("notes"),
            organization_id=actor_org_id or item.get("organization_id"),
            owner_id=item.get("owner_id"),
        )
        session.add(client)
        await session.flush()
        for field_id_str, value in (item.get("custom_values") or {}).items():
            field_result = await session.execute(
                select(CustomField).where(CustomField.id == field_id_str)
            )
            field = field_result.scalar_one_or_none()
            if field:
                session.add(
                    ClientCustomValue(
                        client_id=client.id,
                        field_id=field.id,
                        value=str(value),
                    )
                )
        for tag_name in item.get("tags") or []:
            tag_result = await session.execute(
                select(Tag).where(Tag.name == tag_name)
            )
            tag = tag_result.scalar_one_or_none()
            if tag is None:
                tag = Tag(name=tag_name, organization_id=client.organization_id)
                session.add(tag)
                await session.flush()
            session.add(ClientTag(client_id=client.id, tag_id=tag.id))
        created.append(client)
    await session.commit()
    for client in created:
        await session.refresh(client)
    return created
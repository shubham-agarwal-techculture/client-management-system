"""Client import/export endpoints (JSON and CSV)."""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy import select

from app.api.deps import SessionDep, CurrentUserDep, RequireAgent
from app.models.client import Client
from app.models.user import User
from app.services.import_export import (
    export_clients_csv,
    export_clients_json,
    import_clients_json,
)

router = APIRouter(prefix="/import-export", tags=["import-export"])


@router.get("/export/clients")
async def export_clients(
    session: SessionDep,
    current_user: RequireAgent,
    client_ids: Optional[str] = Query(
        None, description="Comma-separated client IDs; omitting exports all"
    ),
    format: str = Query("json", description="json or csv"),
):
    if client_ids:
        ids = [UUID(x.strip()) for x in client_ids.split(",") if x.strip()]
    else:
        result = await session.execute(select(Client.id))
        ids = [row[0] for row in result.all()]

    if format == "csv":
        content = await export_clients_csv(session, ids)
        media = "text/csv"
        filename = "clients_export.csv"
    else:
        content = await export_clients_json(session, ids)
        media = "application/json"
        filename = "clients_export.json"

    return StreamingResponse(
        iter([content]),
        media_type=media,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/import/clients", status_code=status.HTTP_201_CREATED)
async def import_clients(
    session: SessionDep,
    current_user: RequireAgent,
    file: UploadFile = File(...),
):
    content = (await file.read()).decode("utf-8")
    org_id = current_user.organization_id
    created = await import_clients_json(session, content, actor_org_id=org_id)
    return {"imported": len(created), "ids": [str(c.id) for c in created]}
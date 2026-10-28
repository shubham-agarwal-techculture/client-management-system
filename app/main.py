"""FastAPI application factory for the Client Management System."""

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import app.models.client
import app.models.custom_field
import app.models.client_custom_value
import app.models.tag
import app.models.client_tag
import app.models.organization
import app.models.user
import app.models.interaction
import app.models.task
import app.models.document
import app.models.event_log

from app.config import settings
from app.database import init_db, dispose_db
from app.core.exceptions import (
    CMSError,
    NotFoundError,
    AuthorizationError,
    ValidationError,
)
from app.cli import seed_demo

from app.api.v1 import (
    auth,
    users,
    organizations,
    clients,
    custom_fields,
    tags,
    interactions,
    tasks,
    documents,
    import_export,
)
from app.ui import routes as ui_routes


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    if settings.app_env != "production" and settings.seed_demo_data:
        await seed_demo()
    yield
    await dispose_db()


app = FastAPI(
    title=settings.app_name,
    description="Domain-agnostic, extensible client management system.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(CMSError)
async def cms_error_handler(request: Request, exc: CMSError) -> JSONResponse:
    status = 404 if isinstance(exc, NotFoundError) else (
        403 if isinstance(exc, AuthorizationError) else 400
    )
    return JSONResponse(status_code=status, content={"detail": exc.message})


@app.get("/health", tags=["meta"])
async def health() -> dict[str, Any]:
    return {"status": "ok", "app": settings.app_name, "env": settings.app_env}


@app.get("/", tags=["meta"])
async def root() -> dict[str, str]:
    return {
        "message": "Client Management System API",
        "docs": "/docs",
        "ui": "/ui/",
    }


app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(organizations.router, prefix="/api/v1")
app.include_router(clients.router, prefix="/api/v1")
app.include_router(custom_fields.router, prefix="/api/v1")
app.include_router(tags.router, prefix="/api/v1")
app.include_router(interactions.router, prefix="/api/v1")
app.include_router(tasks.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1")
app.include_router(import_export.router, prefix="/api/v1")
app.include_router(ui_routes.router)
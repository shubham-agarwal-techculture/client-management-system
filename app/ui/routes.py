"""HTMX server-rendered admin UI."""

from typing import Optional

from fastapi import APIRouter, Cookie, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import SessionDep
from app.config import settings
from app.database import async_session_factory, get_session
from app.models.user import User
from app.security import decode_token, get_password_hash, verify_password
from app.services.client_service import ClientService

router = APIRouter(tags=["ui"])
templates = Jinja2Templates(directory="app/ui/templates")


async def _get_user(session: AsyncSession, token: str) -> Optional[User]:
    payload = decode_token(token)
    if not payload or payload.get("typ") == "refresh":
        return None
    result = await session.execute(select(User).where(User.id == payload["sub"]))
    user = result.scalar_one_or_none()
    if user and user.is_active and user.deleted_at is None:
        return user
    return None


async def ui_user(
    request: Request,
    session: AsyncSession = Depends(get_session),
    access_token: Optional[str] = Cookie(None),
) -> User | RedirectResponse:
    if not access_token:
        return RedirectResponse(url="/ui/login", status_code=status.HTTP_303_SEE_OTHER)
    user = await _get_user(session, access_token)
    if not user:
        response = RedirectResponse(url="/ui/login", status_code=status.HTTP_303_SEE_OTHER)
        response.delete_cookie("access_token")
        return response
    return user


@router.get("/ui/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/ui/login")
async def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
):
    from sqlalchemy import select

    async with async_session_factory() as session:
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
    if not user or not verify_password(password, user.hashed_password):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Invalid email or password"},
            status_code=400,
        )
    from app.security import create_access_token, create_refresh_token

    token = create_access_token(user.id)
    response = RedirectResponse(url="/ui/", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        "access_token",
        token,
        httponly=True,
        samesite="lax",
        secure=settings.app_env == "production",
        max_age=settings.access_token_expire_minutes * 60,
    )
    return response


@router.get("/ui/logout")
async def logout():
    response = RedirectResponse(url="/ui/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("access_token")
    return response


@router.get("/ui/", response_class=HTMLResponse)
async def clients_list(
    request: Request,
    user: User = Depends(ui_user),
    session: AsyncSession = Depends(get_session),
    search: Optional[str] = None,
):
    svc = ClientService(session, user)
    from app.core.pagination import PaginationParams

    page = await svc.list(
        PaginationParams(page=1, page_size=25), search=search
    )
    return templates.TemplateResponse(
        "clients/list.html",
        {"request": request, "user": user, "clients": page.items, "search": search or ""},
    )


@router.get("/ui/clients/{client_id}", response_class=HTMLResponse)
async def client_detail(
    request: Request,
    client_id: str,
    user: User = Depends(ui_user),
    session: AsyncSession = Depends(get_session),
):
    from uuid import UUID

    svc = ClientService(session, user)
    client = await svc.get(UUID(client_id), load_relations=True)
    return templates.TemplateResponse(
        "clients/detail.html",
        {"request": request, "user": user, "client": client},
    )


@router.get("/ui/clients/new", response_class=HTMLResponse)
async def client_new_page(request: Request, user: User = Depends(ui_user)):
    return templates.TemplateResponse("clients/form.html", {"request": request, "user": user})


@router.post("/ui/clients")
async def client_create(
    request: Request,
    user: User = Depends(ui_user),
    session: AsyncSession = Depends(get_session),
    name: str = Form(...),
    client_type: Optional[str] = Form(None),
    status: str = Form("active"),
    email: Optional[str] = Form(None),
    phone: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
):
    from app.schemas.client import ClientCreate

    svc = ClientService(session, user)
    await svc.create(
        ClientCreate(
            name=name,
            client_type=client_type,
            status=status,
            email=email,
            phone=phone,
            notes=notes,
            organization_id=user.organization_id,
        )
    )
    return RedirectResponse(url="/ui/", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/ui/clients/{client_id}/delete")
async def client_delete(
    client_id: str,
    user: User = Depends(ui_user),
    session: AsyncSession = Depends(get_session),
):
    from uuid import UUID

    svc = ClientService(session, user)
    await svc.delete(UUID(client_id))
    return RedirectResponse(url="/ui/", status_code=status.HTTP_303_SEE_OTHER)
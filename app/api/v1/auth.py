"""Authentication endpoints: login, refresh, me."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import SessionDep
from app.config import settings
from app.dependencies import get_current_user, require_roles
from app.models.user import User
from app.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from app.schemas.token import LoginRequest, Token
from app.schemas.user import UserRead, UserCreate

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
async def login(session: SessionDep, data: LoginRequest):
    from sqlalchemy import select

    result = await session.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User is inactive"
        )
    return Token(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/refresh", response_model=Token)
async def refresh(session: SessionDep, authorization: str | None = None):
    from sqlalchemy import select

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing refresh token"
        )
    token = authorization.split(" ", 1)[1]
    payload = decode_token(token)
    if not payload or payload.get("typ") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )
    result = await session.execute(select(User).where(User.id == payload["sub"]))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )
    return Token(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.get("/me", response_model=UserRead)
async def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/users", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(
    session: SessionDep,
    data: UserCreate,
    _admin: User = Depends(require_roles("admin")),
):
    from sqlalchemy import select

    result = await session.execute(select(User).where(User.email == data.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already registered"
        )
    user = User(
        email=data.email,
        hashed_password=get_password_hash(data.password),
        full_name=data.full_name,
        role=data.role,
        is_active=data.is_active,
        organization_id=data.organization_id,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user
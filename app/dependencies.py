"""FastAPI dependencies: DB session, current user, pagination, permissions."""

from typing import Annotated, List, Optional

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_session
from app.models.user import User
from app.security import decode_token
from app.core.pagination import PaginationParams


# --- Database ---

DBSession = Annotated[AsyncSession, Depends(get_session)]


# --- Authentication ---

oauth2_scheme = None  # set lazily to avoid importing fastapi.security at module load


def _get_oauth2_scheme():
    global oauth2_scheme
    if oauth2_scheme is None:
        from fastapi.security import OAuth2PasswordBearer

        oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
    return oauth2_scheme


async def get_current_user(
    session: DBSession,
    token: str = Depends(_get_oauth2_scheme),
) -> User:
    """Return the authenticated User for the request, or raise 401."""
    from app.models.user import User
    from sqlalchemy import select

    payload = decode_token(token)
    if payload is None or payload.get("typ") == "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active or user.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return User


CurrentUser = Annotated[User, Depends(get_current_user)]


# --- Authorization ---

def require_roles(*allowed_roles: str):
    """Dependency factory: current user must have one of the allowed roles."""

    def checker(current_user: CurrentUser) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user

    return checker


RequireAdmin = Annotated[User, Depends(require_roles("admin"))]
RequireManager = Annotated[User, Depends(require_roles("admin", "manager"))]
RequireAgent = Annotated[User, Depends(require_roles("admin", "manager", "agent"))]


# --- Pagination ---

def pagination_params(page: int = 1, page_size: int = 20) -> PaginationParams:
    if page < 1:
        page = 1
    if page_size < 1 or page_size > 100:
        page_size = 20
    return PaginationParams(page=page, page_size=page_size)


Pagination = Annotated[PaginationParams, Depends(pagination_params)]
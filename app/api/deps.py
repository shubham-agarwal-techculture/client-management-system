"""API-specific dependencies."""

from typing import Annotated

from fastapi import Depends

from app.dependencies import CurrentUser, DBSession


# Re-export for convenience in routers
CurrentUserDep = CurrentUser
SessionDep = DBSession

from app.dependencies import RequireAgent, RequireManager  # noqa: E402

RequireAgentDep = RequireAgent
RequireManagerDep = RequireManager
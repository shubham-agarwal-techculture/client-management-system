"""Domain-level exceptions used across services and API handlers."""

from typing import Any, Dict, Optional


class CMSError(Exception):
    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code or self.__class__.__name__
        self.details = details or {}


class NotFoundError(CMSError):
    def __init__(self, resource: str, identifier: Any) -> None:
        super().__init__(
            f"{resource} with identifier {identifier!r} not found",
            code="not_found",
            details={"resource": resource, "identifier": str(identifier)},
        )


class AlreadyExistsError(CMSError):
    def __init__(self, resource: str, field: str, value: Any) -> None:
        super().__init__(
            f"{resource} with {field}={value!r} already exists",
            code="already_exists",
            details={"resource": resource, "field": field, "value": str(value)},
        )


class ValidationError(CMSError):
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message,
            code="validation_error",
            details={**(details or {}), **({"field": field} if field else {})},
        )


class AuthorizationError(CMSError):
    def __init__(self, message: str = "Insufficient permissions") -> None:
        super().__init__(message, code="forbidden")


class StorageError(CMSError):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message, code="storage_error", details=details or {})
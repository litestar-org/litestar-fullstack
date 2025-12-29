"""Admin domain for system administration and audit logging."""

from app.domain.admin import controllers, deps, schemas, services

__all__ = (
    "controllers",
    "deps",
    "schemas",
    "services",
)

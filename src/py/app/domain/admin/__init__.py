"""Admin domain for system administration and audit logging."""

from app.domain.admin import controllers, dependencies, schemas, services

__all__ = (
    "controllers",
    "dependencies",
    "schemas",
    "services",
)

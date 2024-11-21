from __future__ import annotations

DB_SESSION_DEPENDENCY_KEY = "db_session"
"""The name of the key used for dependency injection of the database
session."""
USER_DEPENDENCY_KEY = "current_user"
"""The name of the key used for dependency injection of the database
session."""
DTO_INFO_KEY = "info"
"""The name of the key used for storing DTO information."""
DEFAULT_PAGINATION_SIZE = 20
"""Default page size to use."""
CACHE_EXPIRATION: int = 60
"""Default cache key expiration in seconds."""
DEFAULT_USER_ROLE = "Application Access"
"""The name of the default role assigned to all users."""
HEALTH_ENDPOINT = "/health"
"""The endpoint to use for the the service health check."""
SITE_INDEX = "/"
"""The site index URL."""
OPENAPI_SCHEMA = "/schema"
"""The URL path to use for the OpenAPI documentation."""
SUPERUSER_ACCESS_ROLE = "Superuser"
"""The name of the super user role."""

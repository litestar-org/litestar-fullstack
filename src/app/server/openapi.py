from litestar.openapi.config import OpenAPIConfig

from app.__about__ import __version__ as current_version
from app.config import get_settings
from app.domain.security import auth

settings = get_settings()

config = OpenAPIConfig(
    title=settings.app.NAME,
    version=current_version,
    components=[auth.openapi_components],
    security=[auth.security_requirement],
    use_handler_docstrings=True,
    root_schema_site="swagger",
)
"""OpenAPI config for app.  See OpenAPISettings for configuration."""

from litestar.openapi.config import OpenAPIConfig
from litestar.openapi.plugins import ScalarRenderPlugin, SwaggerRenderPlugin

from app.__about__ import __version__ as current_version
from app.config import get_settings
from app.domain.accounts.guards import jwt_auth

settings = get_settings()
config = OpenAPIConfig(
    title=settings.app.NAME,
    version=current_version,
    components=[jwt_auth.openapi_components],
    security=[jwt_auth.security_requirement],
    use_handler_docstrings=True,
    render_plugins=[ScalarRenderPlugin(), SwaggerRenderPlugin()],
)
"""OpenAPI config for app.  See OpenAPISettings for configuration."""

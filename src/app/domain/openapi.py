from starlite.openapi.config import OpenAPIConfig
from starlite.openapi.spec import Contact

from app.domain.security import auth
from app.lib import settings

config = OpenAPIConfig(
    title=settings.openapi.TITLE or settings.app.NAME,
    version=settings.openapi.VERSION,
    contact=Contact(name=settings.openapi.CONTACT_NAME, email=settings.openapi.CONTACT_EMAIL),
    components=[auth.openapi_components],
    security=[auth.security_requirement],
    use_handler_docstrings=True,
    root_schema_site="swagger",
)
"""OpenAPI config for app.  See OpenAPISettings for configuration

Defaults to 'elements' for the documentation.
 It has an interactive 3.1 compliant web app and Swagger does not yet support 3.1
"""

from pydantic_openapi_schema.v3_1_0 import Contact
from starlite import OpenAPIConfig

from app.config import settings
from app.core.security import auth

config = OpenAPIConfig(
    title=settings.openapi.TITLE or settings.app.NAME,
    version=settings.openapi.VERSION,
    contact=Contact(name=settings.openapi.CONTACT_NAME, email=settings.openapi.CONTACT_EMAIL),
    use_handler_docstrings=True,
    root_schema_site="elements",
    components=[auth.openapi_components],
    security=[auth.security_requirement],
)
"""
OpenAPI config for app, see [OpenAPISettings][app.config.OpenAPISettings]

Defaults to 'elements' for the documentation.
 It has an interactive 3.1 compliant web app and Swagger does not yet support 3.1
"""

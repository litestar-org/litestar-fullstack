from pydantic_openapi_schema.v3_1_0 import Contact
from starlite import OpenAPIConfig

from pyspa.config import settings
from pyspa.core.security import oauth2_authentication

config = OpenAPIConfig(
    title=settings.openapi.TITLE or settings.app.NAME,
    version=settings.openapi.VERSION,
    contact=Contact(name=settings.openapi.CONTACT_NAME, email=settings.openapi.CONTACT_EMAIL),
    use_handler_docstrings=True,
    root_schema_site="elements",
    components=[oauth2_authentication.openapi_components],
    security=[oauth2_authentication.security_requirement],
)
"""
OpenAPI config for app, see [OpenAPISettings][starlite_bedrock.config.OpenAPISettings]

Defaults to 'elements' for the documentation.
 It has an interactive 3.1 compliant web app and Swagger does not yet support 3.1
"""

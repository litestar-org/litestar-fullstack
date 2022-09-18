from pydantic_openapi_schema.v3_1_0 import Contact
from starlite import OpenAPIConfig

from pyspa.config import settings
from pyspa.core.security import auth

# auth_openapi_components = Components(
#     securitySchemes={
#         "AccountLogin": SecurityScheme(
#             type="oauth2",
#             name="session",
#             security_scheme_in="cookie",
#             description="OAUTH2 password bearer authentication and authorization.",
#             scheme="Bearer",
#             bearerFormat="JWT",
#             flows=OAuthFlows(
#                 password=OAuthFlow(
#                     tokenUrl=paths.urls.ACCESS_TOKEN,
#                     scopes={},
#                 )
#             ),
#         )
#     }
# )

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
OpenAPI config for app, see [OpenAPISettings][starlite_bedrock.config.OpenAPISettings]

Defaults to 'elements' for the documentation.
 It has an interactive 3.1 compliant web app and Swagger does not yet support 3.1
"""

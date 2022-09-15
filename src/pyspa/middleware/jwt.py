from typing import Dict, Optional, Union

from pydantic import AnyUrl
from pydantic_openapi_schema.v3_1_0 import Components, OAuthFlow, OAuthFlows, SecurityRequirement, SecurityScheme
from starlite_jwt import JWTAuth


class OAuth2PasswordBearerAuth(JWTAuth):
    """Basic Oauth2 Schema for Password Bearer Authentication."""

    openapi_security_scheme_name: str = "AccountLogin"
    """
    The value to use for the OpenAPI security scheme and security requirements
    """
    token_url: Union[str, AnyUrl]
    """
    The URL for retrieving a new token
    """
    scopes: Optional[dict[str, str]] = {}
    """Scopes available for the token"""

    @property
    def oauth_flow(self) -> OAuthFlow:
        """Creates an OpenAPI OAuth2 flow for the password bearer authentication
        schema.

        Returns:
            An [OAuthFlow][pydantic_schema_pydantic.v3_1_0.oauth_flow.OAuthFlow] instance.
        """
        return OAuthFlow(
            tokenUrl=self.token_url,
            scopes=self.scopes,
        )

    @property
    def openapi_components(self) -> Components:
        """Creates OpenAPI documentation for the JWT auth schema used.

        Returns:
            An [Components][pydantic_schema_pydantic.v3_1_0.components.Components] instance.
        """
        return Components(
            securitySchemes={
                self.openapi_security_scheme_name: SecurityScheme(
                    type="oauth2",
                    name=self.auth_header,
                    security_scheme_in="header",
                    description="OAUTH2 password bearer authentication and authorization.",
                    scheme="Bearer",
                    bearerFormat="JWT",
                    flows=OAuthFlows(
                        password=OAuthFlow(
                            tokenUrl=self.token_url,
                            scopes=self.scopes,
                        )
                    ),
                )
            }
        )

    @property
    def security_requirement(self) -> SecurityRequirement:
        """
        Returns:
            An OpenAPI 3.1 [SecurityRequirement][pydantic_schema_pydantic.v3_1_0.security_requirement.SecurityRequirement] dictionary.
        """
        return {self.openapi_security_scheme_name: []}

from typing import TYPE_CHECKING, List, Optional, Union

from pydantic import AnyUrl
from pydantic_openapi_schema.v3_1_0 import Components, OAuthFlow, OAuthFlows, SecurityRequirement, SecurityScheme
from starlite import AbstractAuthenticationMiddleware, AuthenticationResult, NotAuthorizedException
from starlite_jwt import JWTAuth
from starlite_jwt.token import Token

if TYPE_CHECKING:  # pragma: no cover
    from typing import Any, Awaitable, Callable

    from starlette.requests import HTTPConnection
    from starlette.types import ASGIApp


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
        # todo: this may not be correct
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


class JWTAuthenticationMiddleware(AbstractAuthenticationMiddleware):
    def __init__(
        self,
        algorithm: str,
        app: "ASGIApp",
        auth_header: str,
        cookie_name: str,
        retrieve_user_handler: "Callable[[str], Awaitable[Any]]",
        token_secret: str,
        exclude: Optional[Union[str, List[str]]],
    ):
        """This Class is a Starlite compatible JWT authentication middleware.

        It checks incoming requests for an encoded token in the auth header specified,
        and if present retrieves the user from persistence using the provided function.

        Args:
            app: An ASGIApp, this value is the next ASGI handler to call in the middleware stack.
            retrieve_user_handler: A function that receives an instance of 'Token' and returns a user, which can be
                any arbitrary value.
            token_secret: Secret for decoding the JWT token. This value should be equivalent to the secret used to encode it.
            auth_header: Request header key from which to retrieve the token. E.g. 'Authorization' or 'X-Api-Key'.
            algorithm: JWT hashing algorithm to use.
            exclude: A pattern or list of patterns to skip.
        """
        super().__init__(app=app, exclude=exclude)
        self.algorithm = algorithm
        self.auth_header = auth_header
        self.cookie_name = cookie_name
        self.retrieve_user_handler = retrieve_user_handler
        self.token_secret = token_secret

    async def authenticate_request(self, connection: "HTTPConnection") -> AuthenticationResult:
        """Given an HTTP Connection, parse the JWT api key stored in the header
        and retrieve the user correlating to the token from the DB.

        Args:
            connection: An Starlette HTTPConnection instance.

        Returns:
            AuthenticationResult

        Raises:
            [NotAuthorizedException][starlite.exceptions.NotAuthorizedException]: If token is invalid or user is not found.
        """
        auth_header: Optional[str] = connection.headers.get(self.auth_header)
        auth_cookie: Optional[str] = connection.cookies.get(self.cookie_name)
        encoded_token = coalesce([auth_cookie, auth_header])
        if encoded_token:
            token = Token.decode(
                encoded_token=encoded_token,
                secret=self.token_secret,
                algorithm=self.algorithm,
            )
            user = await self.retrieve_user_handler(token.sub)

            if not user:
                raise NotAuthorizedException()

            return AuthenticationResult(user=user, auth=token)
        raise NotAuthorizedException("Authorization required to access")


def coalesce(iterable: list[Optional[str]], default: str | None = None, pred: Any = None) -> str | None:
    """Returns the first non-null value in the iterable.

    If no true value is found, returns *default*

    If *pred* is not None, returns the first item
    for which pred(item) is true.

    """
    # first_true([a,b,c], x) --> a or b or c or x
    # first_true([a,b], x, f) --> a if f(a) else b if f(b) else x
    return next(filter(pred, iterable), default)

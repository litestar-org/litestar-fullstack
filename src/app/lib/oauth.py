# pylint: disable=[invalid-name,import-outside-toplevel]
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, TypeAlias, Union  # noqa: UP035

from httpx_oauth.oauth2 import BaseOAuth2, GetAccessTokenError, OAuth2Error, OAuth2Token
from litestar.exceptions import HTTPException, ImproperlyConfiguredException
from litestar.params import Parameter
from litestar.plugins import InitPluginProtocol
from litestar.status_codes import HTTP_400_BAD_REQUEST, HTTP_500_INTERNAL_SERVER_ERROR

if TYPE_CHECKING:
    import httpx
    from litestar import Request
    from litestar.config.app import AppConfig


AccessTokenState: TypeAlias = tuple[OAuth2Token, str | None]


class OAuth2AuthorizeCallbackError(HTTPException, OAuth2Error):
    """Error raised when an error occurs during the OAuth2 authorization callback.

    It inherits from [HTTPException][litestar.exceptions.HTTPException], so you can either keep
    the default Litestar error handling or implement something dedicated
    """

    def __init__(
        self,
        status_code: int,
        detail: Any = None,
        headers: Union[Dict[str, str], None] = None,  # noqa: UP007, UP006
        response: Union[httpx.Response, None] = None,  # noqa: UP007
    ) -> None:
        self.response = response
        super().__init__(status_code, detail, headers)


class OAuth2AuthorizeCallback:
    """Dependency callable to handle the authorization callback. It reads the query parameters and returns the access token and the state.

    Examples:
        ```py
        from litestar import get
        from httpx_oauth.integrations.litestar import OAuth2AuthorizeCallback
        from httpx_oauth.oauth2 import OAuth2

        client = OAuth2("CLIENT_ID", "CLIENT_SECRET", "AUTHORIZE_ENDPOINT", "ACCESS_TOKEN_ENDPOINT")
        oauth2_authorize_callback = OAuth2AuthorizeCallback(client, "oauth-callback")

        @get("/oauth-callback", name="oauth-callback", dependencies={"access_token_state": Provide(oauth2_authorize_callback)})
        async def oauth_callback(access_token_state: AccessTokenState)) -> Response:
            token, state = access_token_state
            # Do something useful
        ```
    """

    client: BaseOAuth2
    route_name: str | None
    redirect_url: str | None

    def __init__(
        self,
        client: BaseOAuth2,
        route_name: str | None = None,
        redirect_url: str | None = None,
    ) -> None:
        """Args:
        client: An [OAuth2][httpx_oauth.oauth2.BaseOAuth2] client.
        route_name: Name of the callback route, as defined in the `name` parameter of the route decorator.
        redirect_url: Full URL to the callback route.
        """
        if (route_name is not None and redirect_url is not None) or (route_name is None and redirect_url is None):
            raise ImproperlyConfiguredException(
                detail="You should either set route_name or redirect_url",
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            )
        self.client = client
        self.route_name = route_name
        self.redirect_url = redirect_url

    async def __call__(
        self,
        request: Request,
        code: str | None = Parameter(query="code", required=False),
        code_verifier: str | None = Parameter(query="code_verifier", required=False),
        callback_state: str | None = Parameter(query="state", required=False),
        error: str | None = Parameter(query="error", required=False),
    ) -> AccessTokenState:
        if code is None or error is not None:
            raise OAuth2AuthorizeCallbackError(
                status_code=HTTP_400_BAD_REQUEST,
                detail=error if error is not None else None,
            )

        if self.route_name:
            redirect_url = str(request.url_for(self.route_name))
        elif self.redirect_url:
            redirect_url = self.redirect_url

        try:
            access_token = await self.client.get_access_token(
                code,
                redirect_url,
                code_verifier,
            )
        except GetAccessTokenError as e:
            raise OAuth2AuthorizeCallbackError(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                detail=e.message,
                response=e.response,
            ) from e

        return access_token, callback_state


class OAuth2ProviderPlugin(InitPluginProtocol):
    """HTTPX OAuth2 Plugin configuration plugin."""

    def on_app_init(self, app_config: AppConfig) -> AppConfig:
        """Configure application for use with SQLAlchemy.

        Args:
            app_config: The :class:`AppConfig <.config.app.AppConfig>` instance.
        """

        app_config.signature_namespace.update(
            {
                "OAuth2AuthorizeCallback": OAuth2AuthorizeCallback,
                "AccessTokenState": AccessTokenState,
                "OAuth2Token": OAuth2Token,
            },
        )

        return app_config

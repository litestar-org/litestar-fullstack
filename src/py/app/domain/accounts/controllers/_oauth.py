"""OAuth authentication routes - stateless implementation for SPA."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast
from urllib.parse import urlencode

from httpx_oauth.clients.github import GitHubOAuth2
from httpx_oauth.clients.google import GoogleOAuth2
from httpx_oauth.exceptions import GetIdEmailError
from httpx_oauth.oauth2 import BaseOAuth2, GetAccessTokenError, OAuth2Token
from litestar import Controller, get
from litestar.di import Provide
from litestar.exceptions import HTTPException
from litestar.params import Parameter
from litestar.response import Redirect
from litestar.status_codes import HTTP_302_FOUND, HTTP_400_BAD_REQUEST

from app.domain.accounts.deps import provide_users_service
from app.domain.accounts.schemas import OAuthAuthorization
from app.utils.oauth import OAuth2AuthorizeCallback, build_oauth_error_redirect, create_oauth_state, verify_oauth_state

if TYPE_CHECKING:
    from litestar import Request

    from app.domain.accounts.services import UserService
    from app.lib.settings import AppSettings


class OAuthController(Controller):
    """OAuth authentication controller - stateless for SPA.

    Uses signed JWT tokens in the state parameter instead of server sessions.
    This approach is better for SPAs and stateless deployments.
    """

    path = "/api/auth/oauth"
    tags = ["OAuth Authentication"]
    dependencies = {
        "user_service": Provide(provide_users_service),
    }

    @get("/google", name="oauth:google:authorize")
    async def google_authorize(
        self,
        request: Request[Any, Any, Any],
        settings: AppSettings,
        redirect_url: str | None = Parameter(query="redirect_url", required=False),
    ) -> OAuthAuthorization:
        """Initiate Google OAuth flow.

        Args:
            request: The request object
            settings: Application settings
            redirect_url: Frontend callback URL for after authentication

        Raises:
            HTTPException: If OAuth is not configured

        Returns:
            OAuthAuthorization with authorization URL and state
        """
        if not settings.GOOGLE_OAUTH2_CLIENT_ID or not settings.GOOGLE_OAUTH2_CLIENT_SECRET:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail="Google OAuth is not configured",
            )

        client = GoogleOAuth2(
            client_id=settings.GOOGLE_OAUTH2_CLIENT_ID,
            client_secret=settings.GOOGLE_OAUTH2_CLIENT_SECRET,
        )

        frontend_callback = redirect_url or f"{settings.URL}/auth/google/callback"

        state = create_oauth_state(
            provider="google",
            redirect_url=frontend_callback,
            secret_key=settings.SECRET_KEY,
        )

        callback_url = str(request.url_for("oauth:google:callback"))

        authorization_url = await client.get_authorization_url(
            redirect_uri=callback_url,
            state=state,
            scope=["openid", "email", "profile"],
        )

        return OAuthAuthorization(
            authorization_url=authorization_url,
            state=state,
        )

    @get("/google/callback", name="oauth:google:callback")
    async def google_callback(
        self,
        request: Request[Any, Any, Any],
        settings: AppSettings,
        user_service: UserService,
        code: str | None = Parameter(query="code", required=False),
        oauth_state: str | None = Parameter(query="state", required=False),
        oauth_error: str | None = Parameter(query="error", required=False),
    ) -> Redirect:
        """Handle Google OAuth callback.

        Args:
            request: The request object
            settings: Application settings
            user_service: User service
            code: Authorization code from Google
            oauth_state: Signed state token for CSRF protection
            oauth_error: Error message from Google if authorization failed

        Returns:
            Redirect response to frontend with authentication result
        """

        default_callback = f"{settings.URL}/auth/google/callback"
        payload: dict[str, Any] = {}
        frontend_callback = default_callback
        redirect_path = build_oauth_error_redirect(default_callback, "oauth_failed", "Missing state parameter")

        if oauth_state:
            is_valid, payload, error_msg = verify_oauth_state(
                state=oauth_state,
                expected_provider="google",
                secret_key=settings.SECRET_KEY,
            )

            frontend_callback = payload.get("redirect_url", default_callback)
            if not is_valid:
                redirect_path = build_oauth_error_redirect(frontend_callback, "oauth_failed", error_msg)
            elif oauth_error:
                redirect_path = build_oauth_error_redirect(frontend_callback, "oauth_failed", oauth_error)
            elif not code:
                redirect_path = build_oauth_error_redirect(
                    frontend_callback, "oauth_failed", "Missing authorization code"
                )
            else:
                client = GoogleOAuth2(
                    client_id=settings.GOOGLE_OAUTH2_CLIENT_ID,
                    client_secret=settings.GOOGLE_OAUTH2_CLIENT_SECRET,
                )

                callback_url = str(request.url_for("oauth:google:callback"))
                oauth2_callback = OAuth2AuthorizeCallback(
                    cast("BaseOAuth2[OAuth2Token]", client),
                    redirect_url=callback_url,
                )

                try:
                    token_data, _ = await oauth2_callback(request, code=code, callback_state=oauth_state)
                except GetAccessTokenError:
                    redirect_path = build_oauth_error_redirect(
                        frontend_callback, "oauth_failed", "Failed to exchange code for token"
                    )
                else:
                    try:
                        user_id, user_email = await client.get_id_email(token_data["access_token"])
                        user_data = {
                            "id": user_id,
                            "email": user_email,
                        }
                    except GetIdEmailError:
                        redirect_path = build_oauth_error_redirect(
                            frontend_callback, "oauth_failed", "Failed to get user info from Google"
                        )
                    else:
                        user, is_new = await user_service.authenticate_or_create_oauth_user(
                            provider="google",
                            oauth_data=user_data,
                            token_data=token_data,
                        )

                        from app.domain.accounts.guards import create_access_token

                        access_token = create_access_token(
                            user_id=str(user.id),
                            email=user.email,
                            is_superuser=user_service.is_superuser(user),
                            is_verified=user.is_verified,
                            auth_method="oauth",
                        )

                        params = urlencode({"token": access_token, "is_new": str(is_new).lower()})
                        separator = "&" if "?" in frontend_callback else "?"
                        redirect_path = f"{frontend_callback}{separator}{params}"

        return Redirect(
            path=redirect_path,
            status_code=HTTP_302_FOUND,
        )

    @get("/github", name="oauth:github:authorize")
    async def github_authorize(
        self,
        request: Request[Any, Any, Any],
        settings: AppSettings,
        redirect_url: str | None = Parameter(query="redirect_url", required=False),
    ) -> OAuthAuthorization:
        """Initiate GitHub OAuth flow.

        Args:
            request: The request object
            settings: Application settings
            redirect_url: Frontend callback URL for after authentication

        Raises:
            HTTPException: If GitHub OAuth is not configured

        Returns:
            OAuthAuthorization with authorization URL and state
        """
        if not settings.GITHUB_OAUTH2_CLIENT_ID or not settings.GITHUB_OAUTH2_CLIENT_SECRET:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail="GitHub OAuth is not configured",
            )

        client = GitHubOAuth2(
            client_id=settings.GITHUB_OAUTH2_CLIENT_ID,
            client_secret=settings.GITHUB_OAUTH2_CLIENT_SECRET,
        )

        frontend_callback = redirect_url or f"{settings.URL}/auth/github/callback"

        state = create_oauth_state(
            provider="github",
            redirect_url=frontend_callback,
            secret_key=settings.SECRET_KEY,
        )

        callback_url = str(request.url_for("oauth:github:callback"))

        authorization_url = await client.get_authorization_url(
            redirect_uri=callback_url,
            state=state,
            scope=["user:email", "read:user"],
        )

        return OAuthAuthorization(
            authorization_url=authorization_url,
            state=state,
        )

    @get("/github/callback", name="oauth:github:callback")
    async def github_callback(
        self,
        request: Request[Any, Any, Any],
        settings: AppSettings,
        user_service: UserService,
        code: str | None = Parameter(query="code", required=False),
        oauth_state: str | None = Parameter(query="state", required=False),
        oauth_error: str | None = Parameter(query="error", required=False),
        oauth_error_description: str | None = Parameter(query="error_description", required=False),
    ) -> Redirect:
        """Handle GitHub OAuth callback.

        Args:
            request: The request object
            settings: Application settings
            user_service: User service
            code: Authorization code from GitHub
            oauth_state: Signed state token for CSRF protection
            oauth_error: Error code from GitHub if authorization failed
            oauth_error_description: Detailed error message from GitHub

        Returns:
            Redirect response to frontend with authentication result
        """

        default_callback = f"{settings.URL}/auth/github/callback"
        payload: dict[str, Any] = {}
        frontend_callback = default_callback
        redirect_path = build_oauth_error_redirect(default_callback, "oauth_failed", "Missing state parameter")

        if oauth_state:
            is_valid, payload, error_msg = verify_oauth_state(
                state=oauth_state,
                expected_provider="github",
                secret_key=settings.SECRET_KEY,
            )

            frontend_callback = payload.get("redirect_url", default_callback)
            if not is_valid:
                redirect_path = build_oauth_error_redirect(frontend_callback, "oauth_failed", error_msg)
            elif oauth_error:
                error_msg = oauth_error_description or oauth_error
                redirect_path = build_oauth_error_redirect(frontend_callback, "oauth_failed", error_msg)
            elif not code:
                redirect_path = build_oauth_error_redirect(
                    frontend_callback, "oauth_failed", "Missing authorization code"
                )
            else:
                client = GitHubOAuth2(
                    client_id=settings.GITHUB_OAUTH2_CLIENT_ID,
                    client_secret=settings.GITHUB_OAUTH2_CLIENT_SECRET,
                )

                callback_url = str(request.url_for("oauth:github:callback"))
                oauth2_callback = OAuth2AuthorizeCallback(
                    cast("BaseOAuth2[OAuth2Token]", client),
                    redirect_url=callback_url,
                )

                try:
                    token_data, _ = await oauth2_callback(request, code=code, callback_state=oauth_state)
                except GetAccessTokenError:
                    redirect_path = build_oauth_error_redirect(
                        frontend_callback, "oauth_failed", "Failed to exchange code for token"
                    )
                else:
                    try:
                        user_id, user_email = await client.get_id_email(token_data["access_token"])
                        user_data = {
                            "id": user_id,
                            "email": user_email,
                        }
                    except GetIdEmailError:
                        redirect_path = build_oauth_error_redirect(
                            frontend_callback, "oauth_failed", "Failed to get user info from GitHub"
                        )
                    else:
                        user, is_new = await user_service.authenticate_or_create_oauth_user(
                            provider="github",
                            oauth_data=user_data,
                            token_data=token_data,
                        )

                        from app.domain.accounts.guards import create_access_token

                        access_token = create_access_token(
                            user_id=str(user.id),
                            email=user.email,
                            is_superuser=user_service.is_superuser(user),
                            is_verified=user.is_verified,
                            auth_method="oauth",
                        )

                        params = urlencode({"token": access_token, "is_new": str(is_new).lower()})
                        separator = "&" if "?" in frontend_callback else "?"
                        redirect_path = f"{frontend_callback}{separator}{params}"

        return Redirect(
            path=redirect_path,
            status_code=HTTP_302_FOUND,
        )

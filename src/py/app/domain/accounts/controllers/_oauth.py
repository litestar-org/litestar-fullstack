"""OAuth authentication routes - stateless implementation for SPA."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast
from urllib.parse import urlencode
from uuid import UUID

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
from app.domain.accounts.services import UserOAuthAccountService
from app.lib.deps import create_service_dependencies
from app.utils.oauth import OAuth2AuthorizeCallback, build_oauth_error_redirect, create_oauth_state, verify_oauth_state

if TYPE_CHECKING:
    from litestar import Request

    from app.domain.accounts.services import UserService
    from app.lib.settings import AppSettings

# Default scopes for OAuth providers
OAUTH_DEFAULT_SCOPES: dict[str, list[str]] = {
    "google": ["openid", "email", "profile"],
    "github": ["read:user", "user:email"],
}


async def _handle_oauth_link(
    oauth_account_service: UserOAuthAccountService,
    provider: str,
    account_id: str,
    account_email: str | None,
    token_data: dict[str, Any],
    state_user_id: str,
    frontend_callback: str,
    action: str,
) -> str:
    """Handle OAuth account linking flow.

    Returns the redirect path for the response.
    """
    # Check if this OAuth account is already linked to another user
    existing = await oauth_account_service.get_by_provider_account_id(provider, account_id)
    if existing and str(existing.user_id) != state_user_id:
        return build_oauth_error_redirect(
            frontend_callback, "oauth_failed", f"This {provider.title()} account is already linked to another user"
        )

    scopes = token_data.get("scope", "")
    scope_list = scopes.split() if scopes else OAUTH_DEFAULT_SCOPES.get(provider)

    await oauth_account_service.link_or_update_oauth(
        user_id=UUID(state_user_id),
        provider=provider,
        account_id=account_id,
        account_email=account_email,
        access_token=token_data["access_token"],
        refresh_token=token_data.get("refresh_token"),
        expires_at=token_data.get("expires_at"),
        scopes=scope_list,
        provider_user_data={"id": account_id, "email": account_email},
    )

    params = urlencode({"provider": provider, "action": action, "linked": "true"})
    separator = "&" if "?" in frontend_callback else "?"
    return f"{frontend_callback}{separator}{params}"


async def _handle_oauth_login(
    user_service: UserService,
    provider: str,
    account_id: str,
    account_email: str | None,
    token_data: dict[str, Any],
    frontend_callback: str,
) -> str:
    """Handle OAuth login/signup flow.

    Returns the redirect path for the response.
    """
    from app.domain.accounts.guards import create_access_token

    user_data = {"id": account_id, "email": account_email}
    user, is_new = await user_service.authenticate_or_create_oauth_user(
        provider=provider,
        oauth_data=user_data,
        token_data=token_data,
    )

    access_token = create_access_token(
        user_id=str(user.id),
        email=user.email,
        is_superuser=user_service.is_superuser(user),
        is_verified=user.is_verified,
        auth_method="oauth",
    )

    params = urlencode({"token": access_token, "is_new": str(is_new).lower()})
    separator = "&" if "?" in frontend_callback else "?"
    return f"{frontend_callback}{separator}{params}"


class OAuthController(Controller):
    """OAuth authentication controller - stateless for SPA.

    Uses signed JWT tokens in the state parameter instead of server sessions.
    This approach is better for SPAs and stateless deployments.

    Handles both login (for unauthenticated users) and account linking
    (for authenticated users). The action is determined by the 'action'
    field in the state parameter.
    """

    path = "/api/auth/oauth"
    tags = ["OAuth Authentication"]
    dependencies = create_service_dependencies(UserOAuthAccountService, key="oauth_account_service") | {
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
        oauth_account_service: UserOAuthAccountService,
        code: str | None = Parameter(query="code", required=False),
        oauth_state: str | None = Parameter(query="state", required=False),
        oauth_error: str | None = Parameter(query="error", required=False),
    ) -> Redirect:
        """Handle Google OAuth callback for login and account linking."""
        default_callback = f"{settings.URL}/auth/google/callback"
        redirect_path = build_oauth_error_redirect(default_callback, "oauth_failed", "Missing state parameter")

        if not oauth_state:
            return Redirect(path=redirect_path, status_code=HTTP_302_FOUND)

        is_valid, payload, error_msg = verify_oauth_state(oauth_state, "google", settings.SECRET_KEY)
        frontend_callback = payload.get("redirect_url", default_callback)
        action = payload.get("action", "login")

        if not is_valid:
            redirect_path = build_oauth_error_redirect(frontend_callback, "oauth_failed", error_msg)
        elif oauth_error:
            redirect_path = build_oauth_error_redirect(frontend_callback, "oauth_failed", oauth_error)
        elif not code:
            redirect_path = build_oauth_error_redirect(frontend_callback, "oauth_failed", "Missing authorization code")
        else:
            redirect_path = await self._process_google_callback(
                request, settings, user_service, oauth_account_service,
                code, oauth_state, frontend_callback, action, payload
            )

        return Redirect(path=redirect_path, status_code=HTTP_302_FOUND)

    async def _process_google_callback(
        self,
        request: Request[Any, Any, Any],
        settings: AppSettings,
        user_service: UserService,
        oauth_account_service: UserOAuthAccountService,
        code: str,
        oauth_state: str,
        frontend_callback: str,
        action: str,
        payload: dict[str, Any],
    ) -> str:
        """Process Google OAuth callback after validation."""
        client = GoogleOAuth2(settings.GOOGLE_OAUTH2_CLIENT_ID, settings.GOOGLE_OAUTH2_CLIENT_SECRET)
        callback_url = str(request.url_for("oauth:google:callback"))
        oauth2_callback = OAuth2AuthorizeCallback(cast("BaseOAuth2[OAuth2Token]", client), redirect_url=callback_url)

        try:
            token_data, _ = await oauth2_callback(request, code=code, callback_state=oauth_state)
        except GetAccessTokenError:
            return build_oauth_error_redirect(frontend_callback, "oauth_failed", "Failed to exchange code for token")

        try:
            account_id, account_email = await client.get_id_email(token_data["access_token"])
        except GetIdEmailError:
            return build_oauth_error_redirect(frontend_callback, "oauth_failed", "Failed to get user info from Google")

        if action in ("link", "upgrade"):
            state_user_id = payload.get("user_id")
            if not state_user_id:
                return build_oauth_error_redirect(frontend_callback, "oauth_failed", "Invalid OAuth session - missing user")
            return await _handle_oauth_link(
                oauth_account_service, "google", account_id, account_email,
                token_data, state_user_id, frontend_callback, action
            )

        return await _handle_oauth_login(user_service, "google", account_id, account_email, token_data, frontend_callback)

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
        oauth_account_service: UserOAuthAccountService,
        code: str | None = Parameter(query="code", required=False),
        oauth_state: str | None = Parameter(query="state", required=False),
        oauth_error: str | None = Parameter(query="error", required=False),
        oauth_error_description: str | None = Parameter(query="error_description", required=False),
    ) -> Redirect:
        """Handle GitHub OAuth callback for login and account linking."""
        default_callback = f"{settings.URL}/auth/github/callback"
        redirect_path = build_oauth_error_redirect(default_callback, "oauth_failed", "Missing state parameter")

        if not oauth_state:
            return Redirect(path=redirect_path, status_code=HTTP_302_FOUND)

        is_valid, payload, error_msg = verify_oauth_state(oauth_state, "github", settings.SECRET_KEY)
        frontend_callback = payload.get("redirect_url", default_callback)
        action = payload.get("action", "login")

        if not is_valid:
            redirect_path = build_oauth_error_redirect(frontend_callback, "oauth_failed", error_msg)
        elif oauth_error:
            error_msg = oauth_error_description or oauth_error
            redirect_path = build_oauth_error_redirect(frontend_callback, "oauth_failed", error_msg)
        elif not code:
            redirect_path = build_oauth_error_redirect(frontend_callback, "oauth_failed", "Missing authorization code")
        else:
            redirect_path = await self._process_github_callback(
                request, settings, user_service, oauth_account_service,
                code, oauth_state, frontend_callback, action, payload
            )

        return Redirect(path=redirect_path, status_code=HTTP_302_FOUND)

    async def _process_github_callback(
        self,
        request: Request[Any, Any, Any],
        settings: AppSettings,
        user_service: UserService,
        oauth_account_service: UserOAuthAccountService,
        code: str,
        oauth_state: str,
        frontend_callback: str,
        action: str,
        payload: dict[str, Any],
    ) -> str:
        """Process GitHub OAuth callback after validation."""
        client = GitHubOAuth2(settings.GITHUB_OAUTH2_CLIENT_ID, settings.GITHUB_OAUTH2_CLIENT_SECRET)
        callback_url = str(request.url_for("oauth:github:callback"))
        oauth2_callback = OAuth2AuthorizeCallback(cast("BaseOAuth2[OAuth2Token]", client), redirect_url=callback_url)

        try:
            token_data, _ = await oauth2_callback(request, code=code, callback_state=oauth_state)
        except GetAccessTokenError:
            return build_oauth_error_redirect(frontend_callback, "oauth_failed", "Failed to exchange code for token")

        try:
            account_id, account_email = await client.get_id_email(token_data["access_token"])
        except GetIdEmailError:
            return build_oauth_error_redirect(frontend_callback, "oauth_failed", "Failed to get user info from GitHub")

        if action in ("link", "upgrade"):
            state_user_id = payload.get("user_id")
            if not state_user_id:
                return build_oauth_error_redirect(frontend_callback, "oauth_failed", "Invalid OAuth session - missing user")
            return await _handle_oauth_link(
                oauth_account_service, "github", account_id, account_email,
                token_data, state_user_id, frontend_callback, action
            )

        return await _handle_oauth_login(user_service, "github", account_id, account_email, token_data, frontend_callback)

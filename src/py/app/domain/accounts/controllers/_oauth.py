"""OAuth authentication routes - stateless implementation for SPA."""

from __future__ import annotations

import logging
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
from sqlalchemy.orm import undefer_group

from app.domain.accounts.deps import provide_users_service
from app.domain.accounts.guards import create_access_token
from app.domain.accounts.schemas import OAuthAuthorization
from app.domain.accounts.services import UserOAuthAccountService
from app.domain.admin.deps import provide_audit_log_service
from app.lib.deps import create_service_dependencies
from app.utils.oauth import OAuth2AuthorizeCallback, build_oauth_error_redirect, create_oauth_state, verify_oauth_state

if TYPE_CHECKING:
    from litestar import Request

    from app.domain.accounts.services import UserService
    from app.domain.admin.services import AuditLogService
    from app.lib.settings import AppSettings

logger = logging.getLogger(__name__)

OAUTH_DEFAULT_SCOPES: dict[str, list[str]] = {
    "google": ["openid", "email", "profile"],
    "github": ["read:user", "user:email"],
}


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
        "audit_service": Provide(provide_audit_log_service),
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

        frontend_callback = redirect_url or "/auth/google/callback"

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
        audit_service: AuditLogService,
        code: str | None = Parameter(query="code", required=False),
        oauth_state: str | None = Parameter(query="state", required=False),
        oauth_error: str | None = Parameter(query="error", required=False),
    ) -> Redirect:
        """Handle Google OAuth callback for login and account linking.

        Returns:
            Redirect response to the frontend.
        """
        default_callback = "/auth/google/callback"
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
                request,
                settings,
                user_service,
                oauth_account_service,
                audit_service,
                code,
                oauth_state,
                frontend_callback,
                action,
                payload,
            )

        return Redirect(path=redirect_path, status_code=HTTP_302_FOUND)

    async def _process_google_callback(  # noqa: PLR0911
        self,
        request: Request[Any, Any, Any],
        settings: AppSettings,
        user_service: UserService,
        oauth_account_service: UserOAuthAccountService,
        audit_service: AuditLogService,
        code: str,
        oauth_state: str,
        frontend_callback: str,
        action: str,
        payload: dict[str, Any],
    ) -> str:
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

        if action == "mfa_disable":
            state_user_id = payload.get("user_id")
            if not state_user_id:
                return build_oauth_error_redirect(
                    frontend_callback, "oauth_failed", "Invalid OAuth session - missing user"
                )
            return await _handle_mfa_disable(
                user_service,
                oauth_account_service,
                audit_service,
                "google",
                account_id,
                account_email,
                state_user_id,
                frontend_callback,
                request,
            )

        if action in {"link", "upgrade"}:
            state_user_id = payload.get("user_id")
            if not state_user_id:
                return build_oauth_error_redirect(
                    frontend_callback, "oauth_failed", "Invalid OAuth session - missing user"
                )
            return await _handle_oauth_link(
                oauth_account_service,
                "google",
                account_id,
                account_email,
                token_data,
                state_user_id,
                frontend_callback,
                action,
            )
        return await _handle_oauth_login(
            user_service, "google", account_id, account_email, token_data, frontend_callback
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
        state = create_oauth_state(
            provider="github",
            redirect_url=redirect_url or "/auth/github/callback",
            secret_key=settings.SECRET_KEY,
        )
        authorization_url = await client.get_authorization_url(
            redirect_uri=str(request.url_for("oauth:github:callback")),
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
        audit_service: AuditLogService,
        code: str | None = Parameter(query="code", required=False),
        oauth_state: str | None = Parameter(query="state", required=False),
        oauth_error: str | None = Parameter(query="error", required=False),
        oauth_error_description: str | None = Parameter(query="error_description", required=False),
    ) -> Redirect:
        """Handle GitHub OAuth callback for login and account linking.

        Returns:
            Redirect response to the frontend.
        """
        default_callback = "/auth/github/callback"
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
                request,
                settings,
                user_service,
                oauth_account_service,
                audit_service,
                code,
                oauth_state,
                frontend_callback,
                action,
                payload,
            )

        return Redirect(path=redirect_path, status_code=HTTP_302_FOUND)

    async def _process_github_callback(  # noqa: PLR0911
        self,
        request: Request[Any, Any, Any],
        settings: AppSettings,
        user_service: UserService,
        oauth_account_service: UserOAuthAccountService,
        audit_service: AuditLogService,
        code: str,
        oauth_state: str,
        frontend_callback: str,
        action: str,
        payload: dict[str, Any],
    ) -> str:
        """Process GitHub OAuth callback after validation.

        Args:
            request: The request object
            settings: Application settings
            user_service: User service
            oauth_account_service: OAuth account service
            audit_service: Audit log service
            code: Authorization code from GitHub
            oauth_state: State parameter from OAuth flow
            frontend_callback: Frontend callback URL
            action: Action to perform (login, link, upgrade, mfa_disable)
            payload: Decoded state payload

        Returns:
            The redirect path for the response.

        """
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

        if action == "mfa_disable":
            state_user_id = payload.get("user_id")
            if not state_user_id:
                return build_oauth_error_redirect(
                    frontend_callback, "oauth_failed", "Invalid OAuth session - missing user"
                )
            return await _handle_mfa_disable(
                user_service,
                oauth_account_service,
                audit_service,
                "github",
                account_id,
                account_email,
                state_user_id,
                frontend_callback,
                request,
            )

        if action in {"link", "upgrade"}:
            state_user_id = payload.get("user_id")
            if not state_user_id:
                return build_oauth_error_redirect(
                    frontend_callback, "oauth_failed", "Invalid OAuth session - missing user"
                )
            return await _handle_oauth_link(
                oauth_account_service,
                "github",
                account_id,
                account_email,
                token_data,
                state_user_id,
                frontend_callback,
                action,
            )

        return await _handle_oauth_login(
            user_service, "github", account_id, account_email, token_data, frontend_callback
        )


async def _handle_oauth_link(
    oauth_account_service: UserOAuthAccountService,
    provider: str,
    account_id: str,
    account_email: str | None,
    token_data: OAuth2Token,
    state_user_id: str,
    frontend_callback: str,
    action: str,
) -> str:
    """Handle OAuth account linking flow.

    Args:
        oauth_account_service: OAuth account service
        provider: OAuth provider name
        account_id: Provider account ID
        account_email: Provider account email
        token_data: OAuth token data
        state_user_id: User ID from state
        frontend_callback: Callback URL
        action: Action to perform (link)

    Returns:
        The redirect path for the response.
    """
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
    token_data: OAuth2Token,
    frontend_callback: str,
) -> str:
    """Handle OAuth login/signup flow.

    Args:
        user_service: User service
        provider: OAuth provider name
        account_id: Provider account ID
        account_email: Provider account email
        token_data: OAuth token data
        frontend_callback: Callback URL

    Returns:
        The redirect path for the response.
    """
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


async def _handle_mfa_disable(
    user_service: UserService,
    oauth_account_service: UserOAuthAccountService,
    audit_service: AuditLogService,
    provider: str,
    account_id: str,
    _account_email: str | None,
    state_user_id: str,
    frontend_callback: str,
    request: Request[Any, Any, Any],
) -> str:
    """Handle MFA disable via OAuth verification.

    Args:
        user_service: User service
        oauth_account_service: OAuth account service
        audit_service: Audit log service
        provider: OAuth provider name
        account_id: Provider account ID
        _account_email: Provider account email (unused, kept for API consistency)
        state_user_id: User ID from state
        frontend_callback: Callback URL
        request: Request object

    Returns:
        The redirect path for the response.
    """
    # 1. Verify OAuth account belongs to user
    oauth_account = await oauth_account_service.get_one_or_none(
        user_id=UUID(state_user_id),
        oauth_name=provider,
        account_id=account_id,
    )

    if not oauth_account:
        return build_oauth_error_redirect(
            frontend_callback, "oauth_failed", f"This {provider.title()} account is not linked to your user"
        )

    # 2. Get user and verify no password (double check)
    user = await user_service.get(UUID(state_user_id), load=[undefer_group("security_sensitive")])
    if user.hashed_password:
        return build_oauth_error_redirect(
            frontend_callback, "oauth_failed", "Password verification required for users with passwords"
        )

    # 3. Disable MFA
    logger.info("Disabling MFA via OAuth for user %s", user.id)
    await user_service.update(
        {
            "is_two_factor_enabled": False,
            "totp_secret": None,
            "two_factor_confirmed_at": None,
            "backup_codes": None,
        },
        item_id=user.id,
    )
    # Explicitly commit to ensure changes are persisted immediately
    await user_service.repository.session.commit()

    # 4. Log audit event
    await audit_service.log_action(
        action="mfa.disabled.oauth",
        actor_id=user.id,
        actor_email=user.email,
        target_type="user",
        target_id=str(user.id),
        request=request,
        details={"provider": provider},
    )

    # 5. Log user in (create token)
    access_token = create_access_token(
        user_id=str(user.id),
        email=user.email,
        is_superuser=user_service.is_superuser(user),
        is_verified=user.is_verified,
        auth_method="oauth_mfa_disable",
    )

    params = urlencode(
        {
            "token": access_token,
            "message": "MFA disabled successfully",
            "action": "mfa_disable",
            "success": "true",
        }
    )
    separator = "&" if "?" in frontend_callback else "?"
    return f"{frontend_callback}{separator}{params}"

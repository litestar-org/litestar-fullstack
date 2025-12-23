"""OAuth authentication routes - stateless implementation for SPA."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Annotated, Any, cast
from urllib.parse import urlencode

import jwt
from httpx_oauth.clients.github import GitHubOAuth2
from httpx_oauth.clients.google import GoogleOAuth2
from httpx_oauth.exceptions import GetIdEmailError
from httpx_oauth.oauth2 import BaseOAuth2, GetAccessTokenError, OAuth2Token
from litestar import Controller, get, post
from litestar.di import Provide
from litestar.enums import RequestEncodingType
from litestar.exceptions import HTTPException
from litestar.params import Body, Parameter
from litestar.response import Redirect
from litestar.status_codes import HTTP_302_FOUND, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

from app.domain.accounts.dependencies import provide_user_oauth_service, provide_users_service
from app.domain.accounts.schemas import OAuthAccountInfo, OAuthAuthorizationResponse, OAuthLinkRequest
from app.lib.settings import provide_app_settings
from app.utils.oauth import OAuth2AuthorizeCallback

if TYPE_CHECKING:
    from litestar import Request
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.db.models import User
    from app.domain.accounts.services import UserOAuthAccountService, UserService
    from app.lib.settings import AppSettings

# OAuth state token expiration (10 minutes)
OAUTH_STATE_EXPIRY_SECONDS = 600


def _create_oauth_state(
    provider: str,
    redirect_url: str,
    secret_key: str,
) -> str:
    """Create a signed JWT state token for OAuth.

    Args:
        provider: OAuth provider name (google, github)
        redirect_url: Frontend callback URL
        secret_key: Secret key for signing

    Returns:
        Signed JWT state token
    """
    payload = {
        "provider": provider,
        "redirect_url": redirect_url,
        "exp": int(time.time()) + OAUTH_STATE_EXPIRY_SECONDS,
        "iat": int(time.time()),
    }
    return jwt.encode(payload, secret_key, algorithm="HS256")


def _verify_oauth_state(
    state: str,
    expected_provider: str,
    secret_key: str,
) -> tuple[bool, str, str]:
    """Verify and decode OAuth state token.

    Args:
        state: The state token to verify
        expected_provider: Expected OAuth provider
        secret_key: Secret key for verification

    Returns:
        Tuple of (is_valid, redirect_url, error_message)
    """
    try:
        payload = jwt.decode(state, secret_key, algorithms=["HS256"])

        if payload.get("provider") != expected_provider:
            return False, "", "Invalid OAuth provider"

        redirect_url = payload.get("redirect_url", "")
        return True, redirect_url, ""

    except jwt.ExpiredSignatureError:
        return False, "", "OAuth session expired"
    except jwt.InvalidTokenError:
        return False, "", "Invalid OAuth state"


def _build_error_redirect(base_url: str, error: str, message: str) -> str:
    """Build error redirect URL with proper encoding.

    Args:
        base_url: Base redirect URL
        error: Error code
        message: Error message

    Returns:
        Complete redirect URL with error parameters
    """
    params = urlencode({"error": error, "message": message})
    separator = "&" if "?" in base_url else "?"
    return f"{base_url}{separator}{params}"


class OAuthController(Controller):
    """OAuth authentication controller - stateless for SPA.

    Uses signed JWT tokens in the state parameter instead of server sessions.
    This approach is better for SPAs and stateless deployments.
    """

    path = "/api/auth/oauth"
    tags = ["OAuth Authentication"]
    dependencies = {
        "user_service": Provide(provide_users_service),
        "oauth_account_service": Provide(provide_user_oauth_service),
        "settings": Provide(provide_app_settings, sync_to_thread=False),
    }

    @get("/google", name="oauth:google:authorize")
    async def google_authorize(
        self,
        request: Request[Any, Any, Any],
        settings: AppSettings,
        redirect_url: str | None = Parameter(query="redirect_url", required=False),
    ) -> OAuthAuthorizationResponse:
        """Initiate Google OAuth flow.

        Args:
            request: The request object
            settings: Application settings
            redirect_url: Frontend callback URL for after authentication

        Raises:
            HTTPException: If OAuth is not configured

        Returns:
            OAuthAuthorizationResponse with authorization URL and state
        """
        if not settings.GOOGLE_OAUTH2_CLIENT_ID or not settings.GOOGLE_OAUTH2_CLIENT_SECRET:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail="Google OAuth is not configured",
            )

        # Create OAuth client
        client = GoogleOAuth2(
            client_id=settings.GOOGLE_OAUTH2_CLIENT_ID,
            client_secret=settings.GOOGLE_OAUTH2_CLIENT_SECRET,
        )

        # Use provided redirect URL or default to frontend callback
        frontend_callback = redirect_url or f"{settings.URL}/auth/google/callback"

        # Create signed state token (stateless - no session required)
        state = _create_oauth_state(
            provider="google",
            redirect_url=frontend_callback,
            secret_key=settings.SECRET_KEY,
        )

        # Generate backend callback URL
        callback_url = str(request.url_for("oauth:google:callback"))

        # Get authorization URL
        authorization_url = await client.get_authorization_url(
            redirect_uri=callback_url,
            state=state,
            scope=["openid", "email", "profile"],
        )

        return OAuthAuthorizationResponse(
            authorization_url=authorization_url,
            state=state,
        )

    @get("/google/callback", name="oauth:google:callback")
    async def google_callback(
        self,
        request: Request[Any, Any, Any],
        session: AsyncSession,
        settings: AppSettings,
        user_service: UserService,
        oauth_account_service: UserOAuthAccountService,
        code: str | None = Parameter(query="code", required=False),
        oauth_state: str | None = Parameter(query="state", required=False),
        error: str | None = Parameter(query="error", required=False),
    ) -> Redirect:
        """Handle Google OAuth callback.

        Args:
            request: The request object
            session: Database session
            settings: Application settings
            user_service: User service
            oauth_account_service: OAuth account service
            code: Authorization code from Google
            oauth_state: Signed state token for CSRF protection
            error: Error message from Google if authorization failed

        Returns:
            Redirect response to frontend with authentication result
        """
        # Default fallback URL
        default_callback = f"{settings.URL}/auth/google/callback"

        # Verify state and extract redirect URL
        if not oauth_state:
            return Redirect(
                path=_build_error_redirect(default_callback, "oauth_failed", "Missing state parameter"),
                status_code=HTTP_302_FOUND,
            )

        is_valid, frontend_callback, error_msg = _verify_oauth_state(
            state=oauth_state,
            expected_provider="google",
            secret_key=settings.SECRET_KEY,
        )

        if not is_valid:
            return Redirect(
                path=_build_error_redirect(frontend_callback or default_callback, "oauth_failed", error_msg),
                status_code=HTTP_302_FOUND,
            )

        # Check for errors from OAuth provider
        if error:
            return Redirect(
                path=_build_error_redirect(frontend_callback, "oauth_failed", error),
                status_code=HTTP_302_FOUND,
            )

        if not code:
            return Redirect(
                path=_build_error_redirect(frontend_callback, "oauth_failed", "Missing authorization code"),
                status_code=HTTP_302_FOUND,
            )

        # Create OAuth client
        client = GoogleOAuth2(
            client_id=settings.GOOGLE_OAUTH2_CLIENT_ID,
            client_secret=settings.GOOGLE_OAUTH2_CLIENT_SECRET,
        )

        # Exchange code for token
        callback_url = str(request.url_for("oauth:google:callback"))
        oauth2_callback = OAuth2AuthorizeCallback(
            cast("BaseOAuth2[OAuth2Token]", client),
            redirect_url=callback_url,
        )

        try:
            token_data, _ = await oauth2_callback(request, code=code, callback_state=oauth_state)
        except GetAccessTokenError:
            return Redirect(
                path=_build_error_redirect(frontend_callback, "oauth_failed", "Failed to exchange code for token"),
                status_code=HTTP_302_FOUND,
            )

        # Get user info from Google
        try:
            user_id, user_email = await client.get_id_email(token_data["access_token"])
            user_data = {
                "id": user_id,
                "email": user_email,
            }
        except GetIdEmailError:
            return Redirect(
                path=_build_error_redirect(frontend_callback, "oauth_failed", "Failed to get user info from Google"),
                status_code=HTTP_302_FOUND,
            )

        # Authenticate or create user
        user, is_new = await user_service.authenticate_or_create_oauth_user(
            provider="google",
            oauth_data=user_data,
            token_data=token_data,
        )

        # Create JWT token for the user
        from app.domain.accounts.guards import create_access_token

        access_token = create_access_token(
            user_id=str(user.id),
            email=user.email,
            is_superuser=user_service.is_superuser(user),
            is_verified=user.is_verified,
            auth_method="oauth",
        )

        # Redirect to frontend callback with token
        params = urlencode({"token": access_token, "is_new": str(is_new).lower()})
        separator = "&" if "?" in frontend_callback else "?"
        return Redirect(
            path=f"{frontend_callback}{separator}{params}",
            status_code=HTTP_302_FOUND,
        )

    @get("/github", name="oauth:github:authorize")
    async def github_authorize(
        self,
        request: Request[Any, Any, Any],
        settings: AppSettings,
        redirect_url: str | None = Parameter(query="redirect_url", required=False),
    ) -> OAuthAuthorizationResponse:
        """Initiate GitHub OAuth flow.

        Args:
            request: The request object
            settings: Application settings
            redirect_url: Frontend callback URL for after authentication

        Raises:
            HTTPException: If GitHub OAuth is not configured

        Returns:
            OAuthAuthorizationResponse with authorization URL and state
        """
        if not settings.GITHUB_OAUTH2_CLIENT_ID or not settings.GITHUB_OAUTH2_CLIENT_SECRET:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail="GitHub OAuth is not configured",
            )

        # Create OAuth client
        client = GitHubOAuth2(
            client_id=settings.GITHUB_OAUTH2_CLIENT_ID,
            client_secret=settings.GITHUB_OAUTH2_CLIENT_SECRET,
        )

        # Use provided redirect URL or default to frontend callback
        frontend_callback = redirect_url or f"{settings.URL}/auth/github/callback"

        # Create signed state token (stateless - no session required)
        state = _create_oauth_state(
            provider="github",
            redirect_url=frontend_callback,
            secret_key=settings.SECRET_KEY,
        )

        # Generate backend callback URL
        callback_url = str(request.url_for("oauth:github:callback"))

        # Get authorization URL with appropriate scopes for user info
        authorization_url = await client.get_authorization_url(
            redirect_uri=callback_url,
            state=state,
            scope=["user:email", "read:user"],
        )

        return OAuthAuthorizationResponse(
            authorization_url=authorization_url,
            state=state,
        )

    @get("/github/callback", name="oauth:github:callback")
    async def github_callback(
        self,
        request: Request[Any, Any, Any],
        session: AsyncSession,
        settings: AppSettings,
        user_service: UserService,
        oauth_account_service: UserOAuthAccountService,
        code: str | None = Parameter(query="code", required=False),
        oauth_state: str | None = Parameter(query="state", required=False),
        error: str | None = Parameter(query="error", required=False),
        error_description: str | None = Parameter(query="error_description", required=False),
    ) -> Redirect:
        """Handle GitHub OAuth callback.

        Args:
            request: The request object
            session: Database session
            settings: Application settings
            user_service: User service
            oauth_account_service: OAuth account service
            code: Authorization code from GitHub
            oauth_state: Signed state token for CSRF protection
            error: Error code from GitHub if authorization failed
            error_description: Detailed error message from GitHub

        Returns:
            Redirect response to frontend with authentication result
        """
        # Default fallback URL
        default_callback = f"{settings.URL}/auth/github/callback"

        # Verify state and extract redirect URL
        if not oauth_state:
            return Redirect(
                path=_build_error_redirect(default_callback, "oauth_failed", "Missing state parameter"),
                status_code=HTTP_302_FOUND,
            )

        is_valid, frontend_callback, error_msg = _verify_oauth_state(
            state=oauth_state,
            expected_provider="github",
            secret_key=settings.SECRET_KEY,
        )

        if not is_valid:
            return Redirect(
                path=_build_error_redirect(frontend_callback or default_callback, "oauth_failed", error_msg),
                status_code=HTTP_302_FOUND,
            )

        # Check for errors from OAuth provider
        if error:
            error_msg = error_description or error
            return Redirect(
                path=_build_error_redirect(frontend_callback, "oauth_failed", error_msg),
                status_code=HTTP_302_FOUND,
            )

        if not code:
            return Redirect(
                path=_build_error_redirect(frontend_callback, "oauth_failed", "Missing authorization code"),
                status_code=HTTP_302_FOUND,
            )

        # Create OAuth client
        client = GitHubOAuth2(
            client_id=settings.GITHUB_OAUTH2_CLIENT_ID,
            client_secret=settings.GITHUB_OAUTH2_CLIENT_SECRET,
        )

        # Exchange code for token
        callback_url = str(request.url_for("oauth:github:callback"))
        oauth2_callback = OAuth2AuthorizeCallback(
            cast("BaseOAuth2[OAuth2Token]", client),
            redirect_url=callback_url,
        )

        try:
            token_data, _ = await oauth2_callback(request, code=code, callback_state=oauth_state)
        except GetAccessTokenError:
            return Redirect(
                path=_build_error_redirect(frontend_callback, "oauth_failed", "Failed to exchange code for token"),
                status_code=HTTP_302_FOUND,
            )

        # Get user info from GitHub
        try:
            user_id, user_email = await client.get_id_email(token_data["access_token"])
            user_data = {
                "id": user_id,
                "email": user_email,
            }
        except GetIdEmailError:
            return Redirect(
                path=_build_error_redirect(frontend_callback, "oauth_failed", "Failed to get user info from GitHub"),
                status_code=HTTP_302_FOUND,
            )

        # Authenticate or create user
        user, is_new = await user_service.authenticate_or_create_oauth_user(
            provider="github",
            oauth_data=user_data,
            token_data=token_data,
        )

        # Create JWT token for the user
        from app.domain.accounts.guards import create_access_token

        access_token = create_access_token(
            user_id=str(user.id),
            email=user.email,
            is_superuser=user_service.is_superuser(user),
            is_verified=user.is_verified,
            auth_method="oauth",
        )

        # Redirect to frontend callback with token
        params = urlencode({"token": access_token, "is_new": str(is_new).lower()})
        separator = "&" if "?" in frontend_callback else "?"
        return Redirect(
            path=f"{frontend_callback}{separator}{params}",
            status_code=HTTP_302_FOUND,
        )

    @post("/link", name="oauth:link")
    async def link_oauth_account(
        self,
        current_user: User,
        settings: AppSettings,
        oauth_account_service: UserOAuthAccountService,
        data: Annotated[OAuthLinkRequest, Body(media_type=RequestEncodingType.JSON)],
    ) -> OAuthAccountInfo:
        """Link OAuth account to current user.

        Args:
            current_user: The authenticated user
            settings: Application settings
            oauth_account_service: OAuth account service
            data: OAuth link request data

        Returns:
            OAuth account information
        """
        # For now, we only support linking from the authorization flow
        # This endpoint would typically be called after the user has authenticated
        # with OAuth and we have their OAuth data in a temporary storage
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="OAuth account linking must be initiated from the authorization flow",
        )

    @post("/unlink", name="oauth:unlink")
    async def unlink_oauth_account(
        self,
        current_user: User,
        oauth_account_service: UserOAuthAccountService,
        data: Annotated[OAuthLinkRequest, Body(media_type=RequestEncodingType.JSON)],
    ) -> dict[str, Any]:
        """Unlink OAuth account from current user.

        Args:
            current_user: The authenticated user
            oauth_account_service: OAuth account service
            data: OAuth unlink request data

        Returns:
            Success message
        """
        # Check if user has a password before unlinking
        if not current_user.hashed_password:
            # Check if this is the only OAuth account
            oauth_accounts = await oauth_account_service.get_user_oauth_accounts(current_user.id)
            if len(oauth_accounts) <= 1:
                raise HTTPException(
                    status_code=HTTP_400_BAD_REQUEST,
                    detail="Cannot unlink the only authentication method. Please set a password first.",
                )

        # Unlink the OAuth account
        success = await oauth_account_service.unlink_oauth_account(
            user_id=current_user.id,
            provider=data.provider,
        )

        if not success:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail=f"No {data.provider} account linked to your profile",
            )

        return {"message": f"Successfully unlinked {data.provider} account"}

    @get("/accounts", name="oauth:accounts")
    async def get_oauth_accounts(
        self,
        current_user: User,
        oauth_account_service: UserOAuthAccountService,
    ) -> list[OAuthAccountInfo]:
        """Get all linked OAuth accounts for current user.

        Args:
            current_user: The authenticated user
            oauth_account_service: OAuth account service

        Returns:
            List of OAuth account information
        """
        oauth_accounts = await oauth_account_service.get_user_oauth_accounts(current_user.id)

        return [
            OAuthAccountInfo(
                provider=account.oauth_name,
                oauth_id=account.account_id,
                email=account.account_email,
                name=None,  # We don't store name in OAuth account
                avatar_url=None,  # We don't store avatar URL
                linked_at=account.created_at,
                last_login_at=account.last_login_at,
            )
            for account in oauth_accounts
        ]

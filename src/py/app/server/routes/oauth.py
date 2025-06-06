"""OAuth authentication routes."""

from __future__ import annotations

import secrets
from typing import TYPE_CHECKING, Any

from httpx_oauth.clients.google import GoogleOAuth2
from litestar import Controller, Response, get, post
from litestar.enums import RequestEncodingType
from litestar.exceptions import HTTPException
from litestar.params import Body, Parameter
from litestar.response import Redirect
from litestar.status_codes import HTTP_302_FOUND, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

from app.schemas import oauth as schemas
from app.utils.oauth import OAuth2AuthorizeCallback

if TYPE_CHECKING:
    from litestar import Request
    from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User
from app.lib.settings import AppSettings
from app.services import UserOAuthAccountService, UserService


class OAuthController(Controller):
    """OAuth authentication controller."""

    path = "/api/auth/oauth"
    tags = ["OAuth Authentication"]

    @get("/google", name="oauth:google:authorize")
    async def google_authorize(
        self,
        request: Request[Any, Any, Any],
        settings: AppSettings,
        redirect_url: str | None = Parameter(query="redirect_url", required=False),
    ) -> schemas.OAuthAuthorizationResponse:
        """Initiate Google OAuth flow.

        Args:
            request: The request object
            settings: Application settings
            redirect_url: Optional URL to redirect to after authentication

        Returns:
            OAuthAuthorizationResponse with authorization URL and state
        """
        if not settings.GOOGLE_OAUTH2_CLIENT_ID or not settings.GOOGLE_OAUTH2_CLIENT_SECRET:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail="OAuth is not configured",
            )

        # Create OAuth client
        client = GoogleOAuth2(
            client_id=settings.GOOGLE_OAUTH2_CLIENT_ID,
            client_secret=settings.GOOGLE_OAUTH2_CLIENT_SECRET,
        )

        # Generate state parameter for CSRF protection
        state = secrets.token_urlsafe(32)

        # Store state in session (you might want to use a cache instead)
        request.session["oauth_state"] = state
        if redirect_url:
            request.session["oauth_redirect_url"] = redirect_url

        # Generate callback URL
        callback_url = str(request.url_for("oauth:google:callback"))

        # Get authorization URL
        authorization_url = await client.get_authorization_url(
            redirect_uri=callback_url,
            state=state,
            scope=["openid", "email", "profile"],
        )

        return schemas.OAuthAuthorizationResponse(
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
        code: str = Parameter(query="code"),
        oauth_state: str | None = Parameter(query="state", required=False),
        error: str | None = Parameter(query="error", required=False),
    ) -> Response:
        """Handle Google OAuth callback.

        Args:
            request: The request object
            session: Database session
            settings: Application settings
            user_service: User service
            oauth_account_service: OAuth account service
            code: Authorization code from Google
            state: State parameter for CSRF protection
            error: Error message from Google if authorization failed

        Returns:
            Redirect response to frontend with authentication result
        """
        # Check for errors from OAuth provider
        if error:
            return Redirect(
                path=f"{settings.URL}/login?error=oauth_failed&message={error}",
                status_code=HTTP_302_FOUND,
            )

        # Verify state parameter
        stored_state = request.session.get("oauth_state")
        if not oauth_state or oauth_state != stored_state:
            return Redirect(
                path=f"{settings.URL}/login?error=oauth_failed&message=Invalid state parameter",
                status_code=HTTP_302_FOUND,
            )

        # Create OAuth client
        client = GoogleOAuth2(
            client_id=settings.GOOGLE_OAUTH2_CLIENT_ID,
            client_secret=settings.GOOGLE_OAUTH2_CLIENT_SECRET,
        )

        # Exchange code for token
        callback_url = str(request.url_for("oauth:google:callback"))
        oauth2_callback = OAuth2AuthorizeCallback(client, redirect_url=callback_url)

        try:
            token_data, _ = await oauth2_callback(request, code=code, callback_state=oauth_state)
        except Exception:
            return Redirect(
                path=f"{settings.URL}/login?error=oauth_failed&message=Failed to exchange code for token",
                status_code=HTTP_302_FOUND,
            )

        # Get user info from Google
        try:
            user_id, user_email = await client.get_id_email(token_data["access_token"])
            user_data = {
                "id": user_id,
                "email": user_email,
            }
        except Exception:
            return Redirect(
                path=f"{settings.URL}/login?error=oauth_failed&message=Failed to get user info",
                status_code=HTTP_302_FOUND,
            )

        # Authenticate or create user
        user, is_new = await user_service.authenticate_or_create_oauth_user(
            provider="google",
            oauth_data=user_data,
            token_data=token_data,
        )

        # Create JWT token for the user
        from app.server.security import create_access_token

        access_token = create_access_token(
            user_id=str(user.id),
            email=user.email,
            is_superuser=user_service.is_superuser(user),
            is_verified=user.is_verified,
            auth_method="oauth",
        )

        # Get redirect URL from session
        redirect_url = request.session.pop("oauth_redirect_url", f"{settings.URL}/home")

        # Clear OAuth state from session
        request.session.pop("oauth_state", None)

        # Redirect to frontend with token
        return Redirect(
            path=f"{redirect_url}?token={access_token}&is_new={str(is_new).lower()}",
            status_code=HTTP_302_FOUND,
        )

    @post("/link", name="oauth:link")
    async def link_oauth_account(
        self,
        current_user: User,
        settings: AppSettings,
        oauth_account_service: UserOAuthAccountService,
        data: schemas.OAuthLinkRequest = Body(media_type=RequestEncodingType.JSON),
    ) -> schemas.OAuthAccountInfo:
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
        data: schemas.OAuthLinkRequest = Body(media_type=RequestEncodingType.JSON),
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
    ) -> list[schemas.OAuthAccountInfo]:
        """Get all linked OAuth accounts for current user.

        Args:
            current_user: The authenticated user
            oauth_account_service: OAuth account service

        Returns:
            List of OAuth account information
        """
        oauth_accounts = await oauth_account_service.get_user_oauth_accounts(current_user.id)

        return [
            schemas.OAuthAccountInfo(
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

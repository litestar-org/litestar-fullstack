"""OAuth account management routes."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Any, cast
from urllib.parse import urlencode

from httpx_oauth.clients.github import GitHubOAuth2
from httpx_oauth.clients.google import GoogleOAuth2
from httpx_oauth.exceptions import GetIdEmailError
from httpx_oauth.oauth2 import BaseOAuth2, GetAccessTokenError, OAuth2Token
from litestar import Controller, delete, get, post
from litestar.di import Provide
from litestar.exceptions import HTTPException
from litestar.params import Dependency, Parameter
from litestar.response import Redirect
from litestar.status_codes import HTTP_302_FOUND, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND
from sqlalchemy.orm import undefer_group

from app.domain.accounts.deps import provide_users_service
from app.domain.accounts.schemas import OAuthAccountInfo, OAuthAuthorization
from app.domain.accounts.services import UserOAuthAccountService
from app.lib.deps import create_service_dependencies
from app.lib.schema import Message
from app.utils.oauth import OAuth2AuthorizeCallback, build_oauth_error_redirect, create_oauth_state, verify_oauth_state

if TYPE_CHECKING:
    from advanced_alchemy.filters import FilterTypes
    from advanced_alchemy.service.pagination import OffsetPagination
    from litestar import Request

    from app.db import models as m
    from app.domain.accounts.services import UserService
    from app.lib.settings import AppSettings

OAUTH_DEFAULT_SCOPES: dict[str, list[str]] = {
    "google": ["openid", "email", "profile"],
    "github": ["read:user", "user:email"],
}


def _get_oauth_client(provider: str, settings: AppSettings) -> GoogleOAuth2 | GitHubOAuth2:
    """Return an OAuth client for the requested provider.

    Raises:
        HTTPException: If the provider is unsupported or not configured.
    """
    if provider == "google":
        if not settings.GOOGLE_OAUTH2_CLIENT_ID or not settings.GOOGLE_OAUTH2_CLIENT_SECRET:
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Google OAuth is not configured")
        return GoogleOAuth2(
            client_id=settings.GOOGLE_OAUTH2_CLIENT_ID,
            client_secret=settings.GOOGLE_OAUTH2_CLIENT_SECRET,
        )
    if provider == "github":
        if not settings.GITHUB_OAUTH2_CLIENT_ID or not settings.GITHUB_OAUTH2_CLIENT_SECRET:
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="GitHub OAuth is not configured")
        return GitHubOAuth2(
            client_id=settings.GITHUB_OAUTH2_CLIENT_ID,
            client_secret=settings.GITHUB_OAUTH2_CLIENT_SECRET,
        )
    raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=f"Unknown OAuth provider: {provider}")


class OAuthAccountController(Controller):
    """OAuth account management for profile settings."""

    path = "/api/profile/oauth"
    tags = ["Profile"]
    dependencies = create_service_dependencies(
        UserOAuthAccountService,
        key="oauth_account_service",
        filters={
            "pagination_type": "limit_offset",
            "pagination_size": 20,
            "created_at": True,
            "sort_field": "created_at",
            "sort_order": "desc",
        },
    ) | {
        "users_service": Provide(provide_users_service),
    }

    @get(operation_id="ProfileOAuthAccounts", path="/accounts")
    async def list_accounts(
        self,
        current_user: m.User,
        oauth_account_service: UserOAuthAccountService,
        filters: Annotated[list[FilterTypes], Dependency(skip_validation=True)],
    ) -> OffsetPagination[OAuthAccountInfo]:
        """List linked OAuth accounts.

        Args:
            current_user: The authenticated user.
            oauth_account_service: OAuth account service.
            filters: Filter and pagination parameters.

        Returns:
            Linked OAuth accounts.
        """
        accounts, total = await oauth_account_service.list_and_count(
            *filters,
            m.UserOAuthAccount.user_id == current_user.id,
        )
        items = [
            {
                "provider": account.oauth_name,
                "oauth_id": account.account_id,
                "email": account.account_email,
                "name": None,
                "avatar_url": None,
                "linked_at": account.created_at,
                "last_login_at": account.last_login_at,
            }
            for account in accounts
        ]
        return oauth_account_service.to_schema(
            data=items,
            total=total,
            filters=filters,
            schema_type=OAuthAccountInfo,
        )

    @post(operation_id="ProfileOAuthLink", path="/{provider:str}/link")
    async def start_link(
        self,
        request: Request[Any, Any, Any],
        current_user: m.User,
        settings: AppSettings,
        provider: str,
        redirect_url: str | None = Parameter(query="redirect_url", required=False),
    ) -> OAuthAuthorization:
        """Start OAuth linking flow.

        Args:
            request: The request object.
            current_user: The authenticated user.
            settings: Application settings.
            provider: OAuth provider name.
            redirect_url: Frontend callback URL after linking.

        Raises:
            HTTPException: If OAuth is not configured or provider is invalid.

        Returns:
            Authorization URL and state.
        """
        client = _get_oauth_client(provider, settings)
        frontend_callback = redirect_url or f"{settings.URL}/profile"
        state = create_oauth_state(
            provider=provider,
            redirect_url=frontend_callback,
            secret_key=settings.SECRET_KEY,
            action="link",
            user_id=str(current_user.id),
        )
        callback_url = str(request.url_for("oauth:profile:complete", provider=provider))
        authorization_url = await client.get_authorization_url(
            redirect_uri=callback_url,
            state=state,
            scope=OAUTH_DEFAULT_SCOPES.get(provider, []),
        )
        return OAuthAuthorization(authorization_url=authorization_url, state=state)

    @get(operation_id="ProfileOAuthComplete", path="/{provider:str}/complete", name="oauth:profile:complete")
    async def complete_link(
        self,
        request: Request[Any, Any, Any],
        current_user: m.User,
        settings: AppSettings,
        oauth_account_service: UserOAuthAccountService,
        provider: str,
        code: str | None = Parameter(query="code", required=False),
        oauth_state: str | None = Parameter(query="state", required=False),
        error: str | None = Parameter(query="error", required=False),
        error_description: str | None = Parameter(query="error_description", required=False),
    ) -> Redirect:
        """Complete OAuth linking flow and redirect back to the profile.

        Args:
            request: The request object.
            current_user: The authenticated user.
            settings: Application settings.
            oauth_account_service: OAuth account service.
            provider: OAuth provider name.
            code: Authorization code from provider.
            oauth_state: Signed state token.
            error: OAuth error code.
            error_description: OAuth error description.

        Raises:
            HTTPException: If OAuth is not configured or provider is invalid.

        Returns:
            Redirect to frontend with success or error parameters.
        """
        default_callback = f"{settings.URL}/profile"
        payload: dict[str, Any] = {}
        frontend_callback = default_callback
        redirect_path = build_oauth_error_redirect(default_callback, "oauth_failed", "Missing state parameter")

        if oauth_state:
            is_valid, payload, error_msg = verify_oauth_state(
                state=oauth_state,
                expected_provider=provider,
                secret_key=settings.SECRET_KEY,
            )
            frontend_callback = payload.get("redirect_url", default_callback)
            if not is_valid:
                redirect_path = build_oauth_error_redirect(frontend_callback, "oauth_failed", error_msg)
            else:
                state_user_id = payload.get("user_id")
                if state_user_id and state_user_id != str(current_user.id):
                    redirect_path = build_oauth_error_redirect(frontend_callback, "oauth_failed", "Invalid OAuth session")
                elif error:
                    error_msg = error_description or error
                    redirect_path = build_oauth_error_redirect(frontend_callback, "oauth_failed", error_msg)
                elif not code:
                    redirect_path = build_oauth_error_redirect(
                        frontend_callback, "oauth_failed", "Missing authorization code"
                    )
                else:
                    client = _get_oauth_client(provider, settings)
                    callback_url = str(request.url_for("oauth:profile:complete", provider=provider))
                    oauth2_callback = OAuth2AuthorizeCallback(
                        cast("BaseOAuth2[OAuth2Token]", client), redirect_url=callback_url
                    )
                    try:
                        token_data, _ = await oauth2_callback(request, code=code, callback_state=oauth_state)
                    except GetAccessTokenError:
                        redirect_path = build_oauth_error_redirect(
                            frontend_callback, "oauth_failed", "Failed to exchange code for token"
                        )
                    else:
                        try:
                            account_id, account_email = await client.get_id_email(token_data["access_token"])
                        except GetIdEmailError:
                            redirect_path = build_oauth_error_redirect(
                                frontend_callback, "oauth_failed", "Failed to get account info"
                            )
                        else:
                            if not account_email:
                                redirect_path = build_oauth_error_redirect(
                                    frontend_callback, "oauth_failed", "OAuth provider did not return email"
                                )
                            else:
                                existing = await oauth_account_service.get_by_provider_account_id(provider, account_id)
                                if existing and existing.user_id != current_user.id:
                                    redirect_path = build_oauth_error_redirect(
                                        frontend_callback, "oauth_failed", "OAuth account already linked"
                                    )
                                else:
                                    scopes = token_data.get("scope", "")
                                    scope_list = scopes.split() if scopes else OAUTH_DEFAULT_SCOPES.get(provider)

                                    await oauth_account_service.link_or_update_oauth(
                                        user_id=current_user.id,
                                        provider=provider,
                                        account_id=account_id,
                                        account_email=account_email,
                                        access_token=token_data["access_token"],
                                        refresh_token=token_data.get("refresh_token"),
                                        expires_at=token_data.get("expires_at"),
                                        scopes=scope_list,
                                        provider_user_data={"id": account_id, "email": account_email},
                                    )

                                    action = payload.get("action", "link")
                                    params = urlencode({"provider": provider, "action": action, "linked": "true"})
                                    separator = "&" if "?" in frontend_callback else "?"
                                    redirect_path = f"{frontend_callback}{separator}{params}"

        return Redirect(path=redirect_path, status_code=HTTP_302_FOUND)

    @delete(operation_id="ProfileOAuthUnlink", path="/{provider:str}", status_code=200)
    async def unlink(
        self,
        current_user: m.User,
        users_service: UserService,
        oauth_account_service: UserOAuthAccountService,
        provider: str,
    ) -> Message:
        """Unlink an OAuth provider from the user's account.

        Args:
            current_user: The authenticated user.
            users_service: User service.
            oauth_account_service: OAuth account service.
            provider: OAuth provider name.

        Raises:
            HTTPException: If unlink is not allowed or provider not found.

        Returns:
            Success message.
        """
        user_with_password = await users_service.get(current_user.id, load=[undefer_group("security_sensitive")])
        can_unlink, reason = await oauth_account_service.can_unlink_oauth(user_with_password)
        if not can_unlink:
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=reason)

        success = await oauth_account_service.unlink_oauth_account(user_id=current_user.id, provider=provider)
        if not success:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail=f"No {provider} account linked to your profile",
            )

        return Message(message=f"Successfully unlinked {provider} account")

    @post(operation_id="ProfileOAuthUpgradeScopes", path="/{provider:str}/upgrade-scopes")
    async def upgrade_scopes(
        self,
        request: Request[Any, Any, Any],
        current_user: m.User,
        settings: AppSettings,
        provider: str,
        redirect_url: str | None = Parameter(query="redirect_url", required=False),
    ) -> OAuthAuthorization:
        """Request expanded OAuth scopes via re-authorization.

        Args:
            request: The request object.
            current_user: The authenticated user.
            settings: Application settings.
            provider: OAuth provider name.
            redirect_url: Frontend callback URL after upgrade.

        Raises:
            HTTPException: If OAuth is not configured or provider is invalid.

        Returns:
            Authorization URL and state.
        """
        client = _get_oauth_client(provider, settings)
        frontend_callback = redirect_url or f"{settings.URL}/profile"
        state = create_oauth_state(
            provider=provider,
            redirect_url=frontend_callback,
            secret_key=settings.SECRET_KEY,
            action="upgrade",
            user_id=str(current_user.id),
        )
        callback_url = str(request.url_for("oauth:profile:complete", provider=provider))
        authorization_url = await client.get_authorization_url(
            redirect_uri=callback_url,
            state=state,
            scope=OAUTH_DEFAULT_SCOPES.get(provider, []),
        )
        return OAuthAuthorization(authorization_url=authorization_url, state=state)


__all__ = ("OAuthAccountController",)

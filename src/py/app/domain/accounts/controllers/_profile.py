"""User profile SecureController."""

from datetime import timedelta
from typing import Any, ClassVar, cast

from litestar import Request, delete, get, patch
from litestar.di import NamedDependency, Provide
from litestar_security import (
    AuthenticationPolicy,
    CurrentUser,
    SecureController,
    SecurityContext,
    SecurityPlugin,
    any_of,
    required,
    requires_assurance,
)

from app.db import models as m
from app.domain.accounts.deps import provide_users_service
from app.domain.accounts.schemas import PasswordUpdate, ProfileUpdate, User
from app.domain.accounts.services import UserService
from app.lib.schema import Message


class ProfileController(SecureController):
    """Handles self-service profile inspection, updates, password rotation, and account deletion."""

    path = "/api/me"
    tags = ["Access"]
    auth: ClassVar[AuthenticationPolicy] = required("session")
    dependencies = {
        "users_service": Provide(provide_users_service),
    }

    @get(
        operation_id="AccountProfile",
        path="",
        summary="User Profile",
        description="Return the authenticated user's profile.",
        opt={"auth": any_of("session", "api-key")},
    )
    async def get_profile(
        self,
        users_service: UserService,
        current_user: CurrentUser[m.User],
        security_context: NamedDependency[SecurityContext],
    ) -> User:
        """Return the authenticated user's profile."""
        _ = security_context
        db_obj = await users_service.get(current_user.id)
        return users_service.to_schema(db_obj, schema_type=User)

    @patch(operation_id="AccountProfileUpdate", path="")
    async def update_profile(
        self,
        current_user: CurrentUser[m.User],
        data: ProfileUpdate,
        users_service: UserService,
    ) -> User:
        """Update editable profile attributes for the authenticated user."""
        db_obj = await users_service.update(data.to_dict(), item_id=current_user.id, auto_commit=True)
        return users_service.to_schema(db_obj, schema_type=User)

    @patch(
        operation_id="AccountPasswordUpdate",
        path="/password",
        guards=[requires_assurance(max_age=timedelta(minutes=5))],
    )
    async def update_password(
        self,
        current_user: CurrentUser[m.User],
        data: PasswordUpdate,
        users_service: UserService,
    ) -> Message:
        """Update the authenticated user's password after step-up verification."""
        await users_service.update_password(data.to_dict(), db_obj=current_user)
        return Message(message="Your password was successfully modified.")

    @delete(
        operation_id="AccountDelete",
        path="",
        guards=[requires_assurance(max_age=timedelta(minutes=5))],
    )
    async def remove_account(
        self,
        request: Request[Any, Any, Any],
        current_user: CurrentUser[m.User],
        users_service: UserService,
    ) -> None:
        """Delete the authenticated user's account, revoke sessions, and clear browser cookies."""
        plugin = cast("SecurityPlugin[m.User]", request.app.plugins.get(SecurityPlugin))
        if plugin.config.local_auth is not None and plugin.config.local_auth.session_auth is not None:
            await plugin.config.local_auth.session_auth.logout(request)
        _ = await users_service.delete(current_user.id, auto_commit=True)

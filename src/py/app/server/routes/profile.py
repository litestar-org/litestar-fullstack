from __future__ import annotations

from typing import TYPE_CHECKING

import structlog
from litestar import Controller, delete, get, patch
from litestar.di import Provide

from app import schemas as s
from app import services
from app.server.deps import provide_users_service
from app.server.security import requires_active_user

if TYPE_CHECKING:
    from app.db import models as m

logger = structlog.get_logger()


class ProfileController(Controller):
    """Handles the login and registration of the application."""

    tags = ["Access"]
    dependencies = {"users_service": Provide(provide_users_service)}

    @get(
        operation_id="AccountProfile",
        path="/api/me",
        guards=[requires_active_user],
        summary="User Profile",
        description="User profile information.",
    )
    async def get_profile(self, users_service: services.UserService, current_user: m.User) -> s.User:
        """User profile.

        Returns:
            s.User: The current user's profile.
        """
        return users_service.to_schema(current_user, schema_type=s.User)

    @patch(operation_id="AccountProfileUpdate", path="/api/me")
    async def update_profile(
        self,
        current_user: m.User,
        data: s.ProfileUpdate,
        users_service: services.UserService,
    ) -> s.User:
        """User Profile.

        Args:
            current_user: The current user.
            data: The profile update data.
            users_service: The users service.

        Returns:
            The response object.
        """
        db_obj = await users_service.update(data, item_id=current_user.id)
        return users_service.to_schema(db_obj, schema_type=s.User)

    @patch(operation_id="AccountPasswordUpdate", path="/api/me/password")
    async def update_password(
        self,
        current_user: m.User,
        data: s.PasswordUpdate,
        users_service: services.UserService,
    ) -> s.Message:
        """Update user password.

        Args:
            current_user: The current user.
            data: The password update data.
            users_service: The users service.

        Returns:
            The response object.
        """
        await users_service.update_password(data.to_dict(), db_obj=current_user)
        return s.Message(message="Your password was successfully modified.")

    @delete(operation_id="AccountDelete", path="/profile/")
    async def remove_account(
        self,
        current_user: m.User,
        users_service: services.UserService,
    ) -> None:
        """Remove your account.

        Args:
            current_user: The current user.
            users_service: The users service.

        """
        _ = await users_service.delete(current_user.id)

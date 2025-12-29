"""User Profile Controllers."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog
from litestar import Controller, delete, get, patch
from litestar.di import Provide

from app.domain.accounts.deps import provide_users_service
from app.domain.accounts.schemas import PasswordUpdate, ProfileUpdate, User
from app.lib.schema import Message

if TYPE_CHECKING:
    from app.db import models as m
    from app.domain.accounts.services import UserService

logger = structlog.get_logger()


class ProfileController(Controller):
    """Handles the current user profile operations."""

    tags = ["Access"]
    dependencies = {
        "users_service": Provide(provide_users_service),
    }

    @get(
        operation_id="AccountProfile",
        path="/api/me",
        summary="User Profile",
        description="User profile information.",
    )
    async def get_profile(self, users_service: UserService, current_user: m.User) -> User:
        """User profile.

        Returns:
            User: The current user's profile.
        """
        return users_service.to_schema(current_user, schema_type=User)

    @patch(operation_id="AccountProfileUpdate", path="/api/me")
    async def update_profile(
        self,
        current_user: m.User,
        data: ProfileUpdate,
        users_service: UserService,
    ) -> User:
        """User Profile.

        Args:
            current_user: The current user.
            data: The profile update data.
            users_service: The users service.

        Returns:
            The response object.
        """
        db_obj = await users_service.update(data, item_id=current_user.id)
        return users_service.to_schema(db_obj, schema_type=User)

    @patch(operation_id="AccountPasswordUpdate", path="/api/me/password")
    async def update_password(
        self,
        current_user: m.User,
        data: PasswordUpdate,
        users_service: UserService,
    ) -> Message:
        """Update user password.

        Args:
            current_user: The current user.
            data: The password update data.
            users_service: The users service.

        Returns:
            The response object.
        """
        await users_service.update_password(data.to_dict(), db_obj=current_user)
        return Message(message="Your password was successfully modified.")

    @delete(operation_id="AccountDelete", path="/profile/")
    async def remove_account(
        self,
        current_user: m.User,
        users_service: UserService,
    ) -> None:
        """Remove your account.

        Args:
            current_user: The current user.
            users_service: The users service.

        """
        _ = await users_service.delete(current_user.id)

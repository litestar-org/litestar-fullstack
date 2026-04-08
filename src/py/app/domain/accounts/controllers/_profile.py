"""User Profile Controllers."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog
from litestar import Controller, delete, get, patch, post
from litestar.datastructures import UploadFile
from litestar.di import Provide
from litestar.enums import RequestEncodingType
from litestar.exceptions import ClientException, NotFoundException, ValidationException
from litestar.params import Body
from litestar.response import Response

from app.domain.accounts.deps import provide_users_service
from app.domain.accounts.schemas import PasswordUpdate, ProfileUpdate, User
from app.lib.schema import Message

if TYPE_CHECKING:
    from app.db import models as m
    from app.domain.accounts.services import UserService

logger = structlog.get_logger()

ALLOWED_AVATAR_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_AVATAR_SIZE = 5 * 1024 * 1024  # 5 MB


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

    @delete(operation_id="AccountDelete", path="/api/me")
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

    @post(
        operation_id="AccountAvatarUpload",
        path="/api/me/avatar",
        summary="Upload Avatar",
        description="Upload or replace the current user's profile picture.",
    )
    async def upload_avatar(
        self,
        current_user: m.User,
        users_service: UserService,
        data: UploadFile = Body(media_type=RequestEncodingType.MULTI_PART),
    ) -> User:
        """Upload or replace the user's avatar.

        Args:
            current_user: The current user.
            data: The uploaded file.
            users_service: The users service.

        Returns:
            The updated user profile.
        """
        content_type = data.content_type
        if content_type not in ALLOWED_AVATAR_TYPES:
            msg = f"Invalid file type '{content_type}'. Allowed: {', '.join(sorted(ALLOWED_AVATAR_TYPES))}"
            raise ValidationException(msg)

        file_data = await data.read()
        if len(file_data) > MAX_AVATAR_SIZE:
            msg = f"File too large. Maximum size is {MAX_AVATAR_SIZE // (1024 * 1024)}MB."
            raise ClientException(msg)

        filename = data.filename or "avatar"
        db_obj = await users_service.upload_avatar(
            db_obj=current_user,
            data=file_data,
            filename=filename,
            content_type=content_type,
        )
        return users_service.to_schema(db_obj, schema_type=User)

    @get(
        operation_id="AccountAvatarGet",
        path="/api/me/avatar",
        summary="Get Avatar",
        description="Retrieve the current user's profile picture.",
    )
    async def get_avatar(self, current_user: m.User) -> Response:
        """Get the current user's avatar image.

        Args:
            current_user: The current user.

        Returns:
            The avatar image bytes.
        """
        if current_user.avatar is None:
            raise NotFoundException("No avatar set.")

        content = await current_user.avatar.get_content_async()
        return Response(
            content=content,
            media_type=current_user.avatar.content_type or "application/octet-stream",
        )

    @delete(
        operation_id="AccountAvatarDelete",
        path="/api/me/avatar",
        summary="Delete Avatar",
        description="Remove the current user's profile picture.",
    )
    async def delete_avatar(
        self,
        current_user: m.User,
        users_service: UserService,
    ) -> Message:
        """Remove the user's avatar.

        Args:
            current_user: The current user.
            users_service: The users service.

        Returns:
            Confirmation message.
        """
        _ = await users_service.remove_avatar(db_obj=current_user)
        return Message(message="Avatar removed successfully.")

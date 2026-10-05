"""User Profile Controllers."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID  # noqa: TC003

import structlog
from litestar import Controller, delete, get, patch, post
from litestar.di import Provide
from litestar.enums import RequestEncodingType
from litestar.exceptions import NotFoundException, ValidationException
from litestar.params import Body
from litestar.response import Response

from app.domain.accounts.deps import provide_users_service
from app.domain.accounts.guards import is_superuser
from app.domain.accounts.schemas import PasswordUpdate, ProfileUpdate, User
from app.lib import constants
from app.lib.schema import Message

if TYPE_CHECKING:
    from litestar.datastructures import UploadFile

    from app.db import models as m
    from app.domain.accounts.services import UserService

logger = structlog.get_logger()

ALLOWED_AVATAR_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
# Headroom over the file cap for the multipart boundary and part headers, so a
# file just under the cap reaches the service-level size check.
AVATAR_REQUEST_OVERHEAD = 64 * 1024


def _detect_image_mime(data: bytes) -> str | None:
    """Sniff magic bytes to identify common image formats.

    Avoids trusting client-supplied Content-Type when storing/serving uploads.
    """
    if data[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return "image/gif"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return None


async def _avatar_response(user: m.User | None) -> Response[bytes]:
    """Build the image response for a user's avatar.

    Args:
        user: The user whose avatar to serve.

    Returns:
        The avatar image bytes.

    Raises:
        NotFoundException: If the user has no avatar or its stored object is missing.
    """
    if user is None or user.avatar is None:
        msg = "No avatar set."
        raise NotFoundException(msg)
    try:
        content = await user.avatar.get_content_async()
    except FileNotFoundError as e:
        # The row can outlive its object: storage writes happen after the DB commit.
        msg = "No avatar set."
        raise NotFoundException(msg) from e
    return Response(
        content=content,
        media_type=user.avatar.content_type or "application/octet-stream",
        headers={"Cache-Control": "private, no-cache"},
    )


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
        request_max_body_size=constants.MAX_AVATAR_BYTES + AVATAR_REQUEST_OVERHEAD,
    )
    async def upload_avatar(
        self,
        current_user: m.User,
        users_service: UserService,
        data: UploadFile = Body(media_type=RequestEncodingType.MULTI_PART),  # noqa: B008
    ) -> User:
        """Upload or replace the user's avatar.

        Args:
            current_user: The current user.
            data: The uploaded file.
            users_service: The users service.

        Returns:
            The updated user profile.

        Raises:
            ValidationException: If the uploaded bytes do not match a supported image format.
        """
        file_data = await data.read()
        detected = _detect_image_mime(file_data)
        if detected is None or detected not in ALLOWED_AVATAR_TYPES:
            allowed = ", ".join(sorted(ALLOWED_AVATAR_TYPES))
            msg = f"Invalid image. Allowed: {allowed}."
            raise ValidationException(msg)

        db_obj = await users_service.upload_avatar(
            db_obj=current_user,
            data=file_data,
            content_type=detected,
        )
        return users_service.to_schema(db_obj, schema_type=User)

    @get(
        operation_id="AccountAvatarGet",
        path="/api/me/avatar",
        summary="Get Avatar",
        description="Retrieve the current user's profile picture.",
    )
    async def get_avatar(self, current_user: m.User) -> Response[bytes]:
        """Get the current user's avatar image.

        Args:
            current_user: The current user.

        Returns:
            The avatar image bytes.
        """
        return await _avatar_response(current_user)

    @get(
        operation_id="UserAvatarGet",
        path="/api/users/{user_id:uuid}/avatar",
        summary="Get User Avatar",
        description="Retrieve a user's profile picture. Available to the user themselves and to superusers.",
    )
    async def get_user_avatar(
        self,
        current_user: m.User,
        users_service: UserService,
        user_id: UUID,
    ) -> Response[bytes]:
        """Get a user's avatar image.

        Args:
            current_user: The current user.
            users_service: The users service.
            user_id: The user whose avatar to fetch.

        Returns:
            The avatar image bytes.

        Raises:
            NotFoundException: If the avatar is missing or the caller may not view it.
        """
        if user_id == current_user.id:
            return await _avatar_response(current_user)
        if not is_superuser(current_user):
            # 404 rather than 403 so the route doesn't reveal which users have avatars.
            msg = "No avatar set."
            raise NotFoundException(msg)
        return await _avatar_response(await users_service.get_one_or_none(id=user_id))

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
    ) -> None:
        """Remove the user's avatar.

        Args:
            current_user: The current user.
            users_service: The users service.

        Raises:
            NotFoundException: If the user has no avatar set.
        """
        if current_user.avatar is None:
            msg = "No avatar set."
            raise NotFoundException(msg)
        _ = await users_service.remove_avatar(db_obj=current_user)

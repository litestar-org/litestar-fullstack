from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import SecretStr
from starlite import NotAuthorizedException

from app.lib import crypt
from app.lib.service import RepositoryService

from .models import User
from .repositories import UserRepository

if TYPE_CHECKING:
    pass

__all__ = ["UserService"]


class UserService(RepositoryService[User]):
    """User Service."""

    repository_type = UserRepository

    async def exists(self, username: str) -> bool:
        """Check if the user exist.

        Args:
            db_session (AsyncSession): _description_
            username (str): username to find.

        Returns:
            bool: True if the user is found.
        """
        user_exists = await self.repository.count(email=username)
        return bool(user_exists is not None and user_exists > 0)

    async def get_by_email(self, email: str) -> User | None:
        """Find a user by email.

        Args:
            email (str): email to find.

        Returns:
            User | None: Return User or None
        """
        return await self.repository.get_one_or_none(email=email)

    async def authenticate(self, username: str, password: SecretStr) -> User:
        """Authenticate a user.

        Args:
            username (str): Username to authenticate
            password (SecretStr): User password

        Raises:
            NotAuthorizedException: Raised when the user doesn't exist, isn't verified, or is not active.

        Returns:
            models.User: The user object
        """
        user_obj = await self.get_by_email(email=username)
        if user_obj is None:
            raise NotAuthorizedException("User not found or password invalid")
        if not user_obj.hashed_password:
            raise NotAuthorizedException("User does not have a configured password.")
        if not await crypt.verify_password(password, user_obj.hashed_password):
            raise NotAuthorizedException("User not found or password invalid")
        if not user_obj.is_active:
            raise NotAuthorizedException("User account is inactive")
        return user_obj

    async def update_password(self, obj_in: dict[str, Any], db_obj: User) -> None:
        """Update stored user password.

        This is only used when not used IAP authentication.

        Args:
            db_session (AsyncSession): _description_
            obj_in (UserPasswordUpdate): _description_
            db_obj (models.User): _description_

        Raises:
            NotAuthorizedException: _description_
        """
        if not db_obj.hashed_password:
            raise NotAuthorizedException("User does not have a configured password.")
        if not await crypt.verify_password(obj_in["current_password"], db_obj.hashed_password):
            raise NotAuthorizedException("Password failed to match")
        if not db_obj.is_active:
            raise NotAuthorizedException("User account is not active")
        db_obj.hashed_password = await crypt.get_password_hash(obj_in["new_password"])
        await self.repository.update(db_obj)

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from litestar.exceptions import ClientException, PermissionDeniedException
from litestar.plugins.sqlalchemy import repository, service

from app.db import models as m
from app.lib import constants, crypt
from app.lib.validation import PasswordValidationError, validate_password_strength

# Security constants
MAX_FAILED_RESET_ATTEMPTS = 5

if TYPE_CHECKING:
    from uuid import UUID

    from httpx_oauth.oauth2 import OAuth2Token


class UserService(service.SQLAlchemyAsyncRepositoryService[m.User]):
    """Handles database operations for users."""

    class Repo(repository.SQLAlchemyAsyncRepository[m.User]):
        """User SQLAlchemy Repository."""

        model_type = m.User

    repository_type = Repo
    default_role = constants.DEFAULT_ACCESS_ROLE
    match_fields = ["email"]

    async def to_model_on_create(self, data: service.ModelDictT[m.User]) -> service.ModelDictT[m.User]:
        return await self._populate_model(data)

    async def to_model_on_update(self, data: service.ModelDictT[m.User]) -> service.ModelDictT[m.User]:
        return await self._populate_model(data)

    async def to_model_on_upsert(self, data: service.ModelDictT[m.User]) -> service.ModelDictT[m.User]:
        return await self._populate_model(data)

    async def authenticate(self, username: str, password: bytes | str) -> m.User:
        """Authenticate a user against the stored hashed password.

        Returns:
            The user object if authentication is successful.

        Raises:
            PermissionDeniedException: If the user is not found, the password is invalid, or the account is inactive.
        """
        db_obj = await self.get_one_or_none(email=username)
        if db_obj is None:
            msg = "User not found or password invalid"
            raise PermissionDeniedException(detail=msg)
        if db_obj.hashed_password is None:
            msg = "User not found or password invalid."
            raise PermissionDeniedException(detail=msg)
        if not await crypt.verify_password(password, db_obj.hashed_password):
            msg = "User not found or password invalid"
            raise PermissionDeniedException(detail=msg)
        if not db_obj.is_active:
            msg = "User account is inactive"
            raise PermissionDeniedException(detail=msg)
        return db_obj

    async def verify_email(self, user_id: UUID, email: str) -> m.User:
        """Mark user's email as verified.

        Args:
            user_id: The user's UUID
            email: The email address that was verified

        Returns:
            The updated user object

        Raises:
            ClientException: If user not found or email doesn't match
        """
        db_obj = await self.get_one_or_none(id=user_id)
        if db_obj is None:
            raise ClientException(detail="User not found", status_code=404)

        if db_obj.email != email:
            raise ClientException(detail="Email address does not match user account", status_code=400)

        db_obj.is_verified = True
        db_obj.verified_at = datetime.now(UTC).date()
        return await self.repository.update(db_obj)

    async def is_email_verified(self, user_id: UUID) -> bool:
        """Check if user's email is verified.

        Args:
            user_id: The user's UUID

        Returns:
            True if email is verified, False otherwise
        """
        db_obj = await self.get_one_or_none(id=user_id)
        return db_obj.is_verified if db_obj else False

    async def require_verified_email(self, user: m.User) -> None:
        """Raise exception if user's email is not verified.

        Args:
            user: The user object to check

        Raises:
            PermissionDeniedException: If email is not verified
        """
        if not user.is_verified:
            msg = "Email verification required"
            raise PermissionDeniedException(detail=msg)

    async def update_password(self, data: dict[str, Any], db_obj: m.User) -> None:
        """Modify stored user password.

        Raises:
            PermissionDeniedException: If the user is not found, the password is invalid, or the account is inactive.
        """
        if db_obj.hashed_password is None:
            msg = "User not found or password invalid."
            raise PermissionDeniedException(detail=msg)
        if not await crypt.verify_password(data["current_password"], db_obj.hashed_password):
            msg = "User not found or password invalid."
            raise PermissionDeniedException(detail=msg)
        if not db_obj.is_active:
            msg = "User account is not active"
            raise PermissionDeniedException(detail=msg)
        db_obj.hashed_password = await crypt.get_password_hash(data["new_password"])
        await self.repository.update(db_obj)

    @staticmethod
    async def has_role_id(db_obj: m.User, role_id: UUID) -> bool:
        """Return true if user has specified role ID"""
        return any(assigned_role.role_id for assigned_role in db_obj.roles if assigned_role.role_id == role_id)

    @staticmethod
    async def has_role(db_obj: m.User, role_name: str) -> bool:
        """Return true if user has specified role ID"""
        return any(assigned_role.role_id for assigned_role in db_obj.roles if assigned_role.role_name == role_name)

    @staticmethod
    def is_superuser(user: m.User) -> bool:
        return bool(
            user.is_superuser
            or any(
                assigned_role.role_name
                for assigned_role in user.roles
                if assigned_role.role_name == constants.SUPERUSER_ACCESS_ROLE
            ),
        )

    async def reset_password_with_token(self, user_id: UUID, new_password: str) -> m.User:
        """Reset user's password using a validated token.

        Args:
            user_id: The user's UUID
            new_password: The new password

        Returns:
            The updated user object

        Raises:
            ClientException: If user not found or password validation fails
        """
        # Validate password strength
        try:
            validate_password_strength(new_password)
        except PasswordValidationError as e:
            raise ClientException(detail=str(e), status_code=400) from e

        db_obj = await self.get_one_or_none(id=user_id)
        if db_obj is None:
            raise ClientException(detail="User not found", status_code=404)

        if not db_obj.is_active:
            raise ClientException(detail="User account is inactive", status_code=403)

        # Update password and reset security fields
        db_obj.hashed_password = await crypt.get_password_hash(new_password)
        db_obj.password_reset_at = datetime.now(UTC)
        db_obj.failed_reset_attempts = 0
        db_obj.reset_locked_until = None

        return await self.repository.update(db_obj)

    async def is_reset_rate_limited(self, user_id: UUID) -> bool:
        """Check if user is rate limited for password resets.

        Args:
            user_id: The user's UUID

        Returns:
            True if user is rate limited, False otherwise
        """
        db_obj = await self.get_one_or_none(id=user_id)
        if db_obj is None:
            return False

        # Check if user is locked due to failed attempts
        return bool(db_obj.reset_locked_until and db_obj.reset_locked_until > datetime.now(UTC))

    async def increment_failed_reset_attempt(self, user_id: UUID) -> None:
        """Increment failed reset attempts counter.

        Args:
            user_id: The user's UUID
        """
        db_obj = await self.get_one_or_none(id=user_id)
        if db_obj is None:
            return

        db_obj.failed_reset_attempts += 1

        # Lock account after max failed attempts for 1 hour
        if db_obj.failed_reset_attempts >= MAX_FAILED_RESET_ATTEMPTS:
            db_obj.reset_locked_until = datetime.now(UTC).replace(hour=datetime.now(UTC).hour + 1)

        await self.repository.update(db_obj)

    async def _populate_model(self, data: service.ModelDictT[m.User]) -> service.ModelDictT[m.User]:
        data = service.schema_dump(data)
        data = await self._populate_with_hashed_password(data)
        return await self._populate_with_role(data)

    async def _populate_with_hashed_password(self, data: service.ModelDictT[m.User]) -> service.ModelDictT[m.User]:
        if service.is_dict(data) and (password := data.pop("password", None)) is not None:
            data["hashed_password"] = await crypt.get_password_hash(password)
        return data

    async def _populate_with_role(self, data: service.ModelDictT[m.User]) -> service.ModelDictT[m.User]:
        if service.is_dict(data) and (role_id := data.pop("role_id", None)) is not None:
            data = await self.to_model(data)
            data.roles.append(m.UserRole(role_id=role_id, assigned_at=datetime.now(UTC)))
        return data

    async def create_user_from_oauth(
        self,
        oauth_data: dict[str, Any],
        provider: str,
        token_data: OAuth2Token,
    ) -> m.User:
        """Create new user from OAuth data.

        Args:
            oauth_data: User data from OAuth provider
            provider: OAuth provider name (e.g., 'google')
            token_data: OAuth token data

        Returns:
            The created user object
        """
        # Extract user info from OAuth data
        email = oauth_data.get("email", "")
        name = oauth_data.get("name", "")

        # Generate username from email if not provided

        # Create user data
        user_data = {
            "email": email,
            "name": name,
            "is_verified": True,  # Email is verified by OAuth provider
            "verified_at": datetime.now(UTC).date(),
            "is_active": True,
        }

        # Create the user
        return await self.create(data=user_data)

    async def authenticate_or_create_oauth_user(
        self,
        provider: str,
        oauth_data: dict[str, Any],
        token_data: OAuth2Token,
    ) -> tuple[m.User, bool]:
        """Authenticate existing OAuth user or create new one.

        Args:
            provider: OAuth provider name
            oauth_data: User data from OAuth provider
            token_data: OAuth token data

        Returns:
            Tuple of (user, is_new_user)
        """
        from app.services._user_oauth_accounts import UserOAuthAccountService

        # Check if user exists by email
        email = oauth_data.get("email", "")
        existing_user = await self.get_one_or_none(email=email) if email else None

        if existing_user:
            # User exists, update OAuth account
            oauth_service = UserOAuthAccountService(session=self.repository.session)
            await oauth_service.create_or_update_oauth_account(
                user_id=existing_user.id,
                provider=provider,
                oauth_data=oauth_data,
                token_data=token_data,
            )
            return existing_user, False

        # Create new user
        new_user = await self.create_user_from_oauth(
            oauth_data=oauth_data,
            provider=provider,
            token_data=token_data,
        )

        # Create OAuth account for new user
        oauth_service = UserOAuthAccountService(session=self.repository.session)
        await oauth_service.create_or_update_oauth_account(
            user_id=new_user.id,
            provider=provider,
            oauth_data=oauth_data,
            token_data=token_data,
        )

        return new_user, True

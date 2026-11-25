"""User account database service."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from advanced_alchemy.extensions.litestar import service
from litestar.exceptions import ClientException, PermissionDeniedException
from litestar_security.accounts import Argon2PasswordHasher
from sqlalchemy import update as sa_update
from sqlalchemy.orm import undefer_group

from app.db import models as m
from app.lib import constants
from app.lib.validation import PasswordValidationError, validate_password_strength

if TYPE_CHECKING:
    from uuid import UUID

    from advanced_alchemy.service import ModelDictT

_PASSWORD_HASHER = Argon2PasswordHasher()


class UserService(service.SQLAlchemyAsyncRepositoryService[m.User]):
    """Handles database operations for user accounts using Argon2 password hashing."""

    default_role = constants.DEFAULT_ACCESS_ROLE
    match_fields = ["email"]

    async def to_model_on_create(self, data: ModelDictT[m.User]) -> ModelDictT[m.User]:
        """Hash plaintext passwords and attach initial role assignments before creation.

        Returns:
            Normalized user payload or model instance ready for persistence.
        """
        return await self._populate_model(data)

    async def to_model_on_update(self, data: ModelDictT[m.User]) -> ModelDictT[m.User]:
        """Hash plaintext passwords when updating a user record.

        Returns:
            Normalized user payload or model instance ready for update.
        """
        return await self._populate_model(data)

    async def to_model_on_upsert(self, data: ModelDictT[m.User]) -> ModelDictT[m.User]:
        """Hash plaintext passwords when upserting a user record.

        Returns:
            Normalized user payload or model instance ready for upsert.
        """
        return await self._populate_model(data)

    async def authenticate(self, username: str, password: str) -> m.User:
        """Verify email and password against the stored Argon2 hash.

        Args:
            username: User email address.
            password: Candidate plaintext password.

        Returns:
            The authenticated active user record.

        Raises:
            PermissionDeniedException: If credentials are invalid or the account is inactive.
        """
        db_obj = await self.get_one_or_none(email=username, load=[undefer_group("security_sensitive")])
        if db_obj is None or db_obj.hashed_password is None:
            msg = "User not found or password invalid"
            raise PermissionDeniedException(detail=msg)
        outcome = await _PASSWORD_HASHER.verify(db_obj.hashed_password, password)
        if not outcome.verified:
            msg = "User not found or password invalid"
            raise PermissionDeniedException(detail=msg)
        if not db_obj.is_active:
            msg = "User account is inactive"
            raise PermissionDeniedException(detail=msg)
        return db_obj

    async def verify_email(self, user_id: UUID, email: str) -> m.User:
        """Mark a user's email address as verified.

        Args:
            user_id: Target user UUID.
            email: Verified email address expected to match the account.

        Returns:
            The updated user record.

        Raises:
            ClientException: If the user does not exist or the email does not match.
        """
        db_obj = await self.get_one_or_none(id=user_id)
        if db_obj is None:
            raise ClientException(detail="User not found", status_code=404)
        if db_obj.email != email:
            raise ClientException(detail="Email address does not match user account", status_code=400)
        db_obj.is_verified = True
        db_obj.verified_at = datetime.now(UTC).date()
        return await self.update(data=db_obj)

    async def update_password(self, data: dict[str, Any], db_obj: m.User) -> None:
        """Verify current password and store a new Argon2 password hash.

        Args:
            data: Mapping containing ``current_password`` and ``new_password``.
            db_obj: Target user record.

        Raises:
            ClientException: If the new password fails strength validation.
            PermissionDeniedException: If current password verification fails or the account is inactive.
        """
        try:
            validate_password_strength(str(data["new_password"]))
        except PasswordValidationError as exc:
            raise ClientException(detail=str(exc), status_code=400) from exc

        loaded = await self.get(db_obj.id, load=[undefer_group("security_sensitive")])
        if loaded.hashed_password is None:
            msg = "User not found or password invalid."
            raise PermissionDeniedException(detail=msg)
        outcome = await _PASSWORD_HASHER.verify(loaded.hashed_password, str(data["current_password"]))
        if not outcome.verified:
            msg = "User not found or password invalid."
            raise PermissionDeniedException(detail=msg)
        if not loaded.is_active:
            msg = "User account is not active"
            raise PermissionDeniedException(detail=msg)
        new_hash = await _PASSWORD_HASHER.hash(str(data["new_password"]))
        now = datetime.now(UTC)
        await self.repository.session.execute(
            sa_update(m.UserSession)
            .where(m.UserSession.user_id == loaded.id, m.UserSession.revoked_at.is_(None))
            .values(revoked_at=now)
        )
        await self.update(
            item_id=loaded.id,
            data={"hashed_password": new_hash, "security_epoch": loaded.security_epoch + 1},
            auto_commit=True,
        )

    @staticmethod
    async def has_role_id(db_obj: m.User, role_id: UUID) -> bool:
        """Return whether the user holds the role identified by ``role_id``."""
        return any(assigned.role_id == role_id for assigned in db_obj.roles)

    @staticmethod
    async def has_role(db_obj: m.User, role_name: str) -> bool:
        """Return whether the user holds the named role."""
        return any(assigned.role_name == role_name for assigned in db_obj.roles)

    @staticmethod
    def is_superuser(user: m.User) -> bool:
        """Return whether the user is a superuser via flag or role assignment."""
        return bool(
            user.is_superuser or any(assigned.role_name == constants.SUPERUSER_ACCESS_ROLE for assigned in user.roles),
        )

    async def _populate_model(self, data: ModelDictT[m.User]) -> ModelDictT[m.User]:
        dumped: ModelDictT[m.User] = service.schema_dump(data)
        dumped = await self._populate_with_hashed_password(dumped)
        return await self._populate_with_role(dumped)

    async def _populate_with_hashed_password(self, data: ModelDictT[m.User]) -> ModelDictT[m.User]:
        if service.is_dict(data) and (password := data.pop("password", None)) is not None:
            data["hashed_password"] = await _PASSWORD_HASHER.hash(str(password))
        return data

    async def _populate_with_role(self, data: ModelDictT[m.User]) -> ModelDictT[m.User]:
        if service.is_dict(data) and (role_id := data.pop("role_id", None)) is not None:
            model = await self.to_model(data)
            model.roles.append(m.UserRole(role_id=role_id, assigned_at=datetime.now(UTC)))
            return model
        return data

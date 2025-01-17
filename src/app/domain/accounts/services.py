from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID  # noqa: TC003

from advanced_alchemy.repository import (
    SQLAlchemyAsyncRepository,
    SQLAlchemyAsyncSlugRepository,
)
from advanced_alchemy.service import (
    ModelDictT,
    SQLAlchemyAsyncRepositoryService,
    is_dict_with_field,
    is_dict_without_field,
    is_schema_with_field,
)
from litestar.exceptions import PermissionDeniedException

from app.config import constants
from app.db import models as m
from app.lib import crypt


class UserService(SQLAlchemyAsyncRepositoryService[m.User]):
    """Handles database operations for users."""

    class UserRepository(SQLAlchemyAsyncRepository[m.User]):
        """User SQLAlchemy Repository."""

        model_type = m.User

    repository_type = UserRepository
    default_role = constants.DEFAULT_USER_ROLE
    match_fields = ["email"]

    async def authenticate(self, username: str, password: bytes | str) -> m.User:
        """Authenticate a user against the stored hashed password."""
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

    async def update_password(self, data: dict[str, Any], db_obj: m.User) -> None:
        """Modify stored user password."""
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
            or any(assigned_role.role.name for assigned_role in user.roles if assigned_role.role.name in {"Superuser"}),
        )

    async def to_model(self, data: ModelDictT[m.User], operation: str | None = None) -> m.User:
        if is_dict_with_field(data, "password"):
            password: bytes | str | None = data.pop("password", None)
            if password is not None:
                data.update({"hashed_password": await crypt.get_password_hash(password)})
        if is_dict_with_field(data, "role_id") and operation in {"create", "update", "upsert"}:
            role_id: UUID | None = data.pop("role_id", None)
            data = await self.to_model(data, operation)
            if role_id:
                data.roles.append(m.UserRole(role_id=role_id, assigned_at=datetime.now(UTC)))
        return await super().to_model(data, operation)


class RoleService(SQLAlchemyAsyncRepositoryService[m.Role]):
    """Handles database operations for users."""

    class Repository(SQLAlchemyAsyncSlugRepository[m.Role]):
        """User SQLAlchemy Repository."""

        model_type = m.Role

    repository_type = Repository
    match_fields = ["name"]

    async def to_model(self, data: ModelDictT[m.Role], operation: str | None = None) -> m.Role:
        data = await self._populate_slug(data, operation)
        return await super().to_model(data, operation)

    async def _populate_slug(self, data: ModelDictT[m.Role], operation: str | None) -> ModelDictT[m.Role]:
        if operation == "create" and is_schema_with_field(data, "slug") and data.slug is None:  # type: ignore[union-attr]
            data.slug = await self.repository.get_available_slug(data.name)  # type: ignore[union-attr]
        if operation == "create" and is_dict_without_field(data, "slug"):
            data["slug"] = await self.repository.get_available_slug(data["name"])
        if operation == "update" and is_schema_with_field(data, "slug") and data.slug is None:  # type: ignore[union-attr]
            data.slug = await self.repository.get_available_slug(data.name)  # type: ignore[ union-attr]
        if operation == "update" and is_dict_without_field(data, "slug") and is_dict_with_field(data, "name"):
            data["slug"] = await self.repository.get_available_slug(data["name"])
        return data


class UserRoleService(SQLAlchemyAsyncRepositoryService[m.UserRole]):
    """Handles database operations for user roles."""

    class Repository(SQLAlchemyAsyncRepository[m.UserRole]):
        """User Role SQLAlchemy Repository."""

        model_type = m.UserRole

    repository_type = Repository


class UserOAuthAccountService(SQLAlchemyAsyncRepositoryService[m.UserOauthAccount]):
    """Handles database operations for user roles."""

    class Repository(SQLAlchemyAsyncRepository[m.UserOauthAccount]):
        """User SQLAlchemy Repository."""

        model_type = m.UserOauthAccount

    repository_type = Repository

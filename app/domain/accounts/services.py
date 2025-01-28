from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID  # noqa: TC003

from litestar.exceptions import PermissionDeniedException
from litestar.plugins.sqlalchemy import repository, service

from app.config import constants
from app.db import models as m
from app.lib import crypt


class UserService(service.SQLAlchemyAsyncRepositoryService[m.User]):
    """Handles database operations for users."""

    class Repo(repository.SQLAlchemyAsyncRepository[m.User]):
        """User SQLAlchemy Repository."""

        model_type = m.User

    repository_type = Repo
    default_role = constants.DEFAULT_USER_ROLE
    match_fields = ["email"]

    async def to_model_on_create(self, data: service.ModelDictT[m.User]) -> service.ModelDictT[m.User]:
        return await self._populate_model(data)

    async def to_model_on_update(self, data: service.ModelDictT[m.User]) -> service.ModelDictT[m.User]:
        return await self._populate_model(data)

    async def to_model_on_upsert(self, data: service.ModelDictT[m.User]) -> service.ModelDictT[m.User]:
        return await self._populate_model(data)

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


class RoleService(service.SQLAlchemyAsyncRepositoryService[m.Role]):
    """Handles database operations for users."""

    class Repo(repository.SQLAlchemyAsyncSlugRepository[m.Role]):
        """User SQLAlchemy Repository."""

        model_type = m.Role

    repository_type = Repo
    match_fields = ["name"]

    async def to_model_on_create(self, data: service.ModelDictT[m.Role]) -> service.ModelDictT[m.Role]:
        data = service.schema_dump(data)
        if service.is_dict_without_field(data, "slug"):
            data["slug"] = await self.repository.get_available_slug(data["name"])
        return data

    async def to_model_on_update(self, data: service.ModelDictT[m.Role]) -> service.ModelDictT[m.Role]:
        data = service.schema_dump(data)
        if service.is_dict_without_field(data, "slug") and service.is_dict_with_field(data, "name"):
            data["slug"] = await self.repository.get_available_slug(data["name"])
        return data

    async def to_model_on_upsert(self, data: service.ModelDictT[m.Role]) -> service.ModelDictT[m.Role]:
        data = service.schema_dump(data)
        if service.is_dict_without_field(data, "slug") and (role_name := data.get("name")) is not None:
            data["slug"] = await self.repository.get_available_slug(role_name)
        return data


class UserRoleService(service.SQLAlchemyAsyncRepositoryService[m.UserRole]):
    """Handles database operations for user roles."""

    class Repo(repository.SQLAlchemyAsyncRepository[m.UserRole]):
        """User Role SQLAlchemy Repository."""

        model_type = m.UserRole

    repository_type = Repo


class UserOAuthAccountService(service.SQLAlchemyAsyncRepositoryService[m.UserOauthAccount]):
    """Handles database operations for user roles."""

    class Repo(repository.SQLAlchemyAsyncRepository[m.UserOauthAccount]):
        """User SQLAlchemy Repository."""

        model_type = m.UserOauthAccount

    repository_type = Repo

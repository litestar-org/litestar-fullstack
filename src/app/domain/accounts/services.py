from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any
from uuid import UUID  # noqa: TCH003

from advanced_alchemy.service import (
    ModelDictT,
    SQLAlchemyAsyncRepositoryService,
    is_dict,
    is_msgspec_model,
    is_pydantic_model,
)
from litestar.exceptions import PermissionDeniedException

from app.config import constants
from app.db.models import Role, User, UserRole
from app.lib import crypt

from .repositories import RoleRepository, UserRepository, UserRoleRepository

if TYPE_CHECKING:
    from collections.abc import Iterable

    from advanced_alchemy.repository._util import LoadSpec
    from sqlalchemy.orm import InstrumentedAttribute


class UserService(SQLAlchemyAsyncRepositoryService[User]):
    """Handles database operations for users."""

    repository_type = UserRepository
    default_role = constants.DEFAULT_USER_ROLE

    def __init__(self, **repo_kwargs: Any) -> None:
        self.repository: UserRepository = self.repository_type(**repo_kwargs)
        self.model_type = self.repository.model_type

    async def create(
        self,
        data: ModelDictT[User],
        *,
        load: LoadSpec | None = None,
        execution_options: dict[str, Any] | None = None,
        auto_commit: bool | None = None,
        auto_expunge: bool | None = None,
        auto_refresh: bool | None = None,
    ) -> User:
        """Create a new User and assign default Role."""
        if isinstance(data, dict):
            role_id: UUID | None = data.pop("role_id", None)
            data = await self.to_model(data, "create")
            if role_id:
                data.roles.append(UserRole(role_id=role_id, assigned_at=datetime.now(timezone.utc)))  # noqa: UP017
        return await super().create(
            data=data,
            load=load,
            execution_options=execution_options,
            auto_commit=auto_commit,
            auto_expunge=auto_expunge,
            auto_refresh=auto_refresh,
        )

    async def update(
        self,
        data: ModelDictT[User],
        item_id: Any | None = None,
        *,
        id_attribute: str | InstrumentedAttribute[Any] | None = None,
        load: LoadSpec | None = None,
        execution_options: dict[str, Any] | None = None,
        attribute_names: Iterable[str] | None = None,
        with_for_update: bool | None = None,
        auto_commit: bool | None = None,
        auto_expunge: bool | None = None,
        auto_refresh: bool | None = None,
    ) -> User:
        if isinstance(data, dict):
            role_id: UUID | None = data.pop("role_id", None)
            data = await self.to_model(data, "update")
            if role_id:
                data.roles.append(UserRole(role_id=role_id, assigned_at=datetime.now(timezone.utc)))  # noqa: UP017
        return await super().update(
            data=data,
            item_id=item_id,
            attribute_names=attribute_names,
            with_for_update=with_for_update,
            auto_commit=auto_commit,
            auto_expunge=auto_expunge,
            auto_refresh=auto_refresh,
            id_attribute=id_attribute,
            load=load,
            execution_options=execution_options,
        )

    async def authenticate(self, username: str, password: bytes | str) -> User:
        """Authenticate a user.

        Args:
            username (str): _description_
            password (str | bytes): _description_

        Raises:
            NotAuthorizedException: Raised when the user doesn't exist, isn't verified, or is not active.

        Returns:
            User: The user object
        """
        db_obj = await self.get_one_or_none(email=username)
        if db_obj is None:
            msg = "User not found or password invalid"
            raise PermissionDeniedException(msg)
        if db_obj.hashed_password is None:
            msg = "User not found or password invalid."
            raise PermissionDeniedException(msg)
        if not await crypt.verify_password(password, db_obj.hashed_password):
            msg = "User not found or password invalid"
            raise PermissionDeniedException(msg)
        if not db_obj.is_active:
            msg = "User account is inactive"
            raise PermissionDeniedException(msg)
        return db_obj

    async def update_password(self, data: dict[str, Any], db_obj: User) -> None:
        """Update stored user password.

        This is only used when not used IAP authentication.

        Args:
            data (UserPasswordUpdate): _description_
            db_obj (User): _description_

        Raises:
            PermissionDeniedException: _description_
        """
        if db_obj.hashed_password is None:
            msg = "User not found or password invalid."
            raise PermissionDeniedException(msg)
        if not await crypt.verify_password(data["current_password"], db_obj.hashed_password):
            msg = "User not found or password invalid."
            raise PermissionDeniedException(msg)
        if not db_obj.is_active:
            msg = "User account is not active"
            raise PermissionDeniedException(msg)
        db_obj.hashed_password = await crypt.get_password_hash(data["new_password"])
        await self.repository.update(db_obj)

    @staticmethod
    def is_superuser(user: User) -> bool:
        return bool(
            user.is_superuser
            or any(
                assigned_role.role.name
                for assigned_role in user.roles
                if assigned_role.role.name in {constants.SUPERUSER_ACCESS_ROLE}
            ),
        )

    async def to_model(self, data: ModelDictT[User], operation: str | None = None) -> User:
        if isinstance(data, dict) and "password" in data:
            password: bytes | str | None = data.pop("password", None)
            if password is not None:
                data.update({"hashed_password": await crypt.get_password_hash(password)})
        return await super().to_model(data, operation)


class RoleService(SQLAlchemyAsyncRepositoryService[Role]):
    """Handles database operations for users."""

    repository_type = RoleRepository
    match_fields = ["name"]

    def __init__(self, **repo_kwargs: Any) -> None:
        self.repository: RoleRepository = self.repository_type(**repo_kwargs)
        self.model_type = self.repository.model_type

    async def to_model(self, data: ModelDictT[Role], operation: str | None = None) -> Role:
        if (is_msgspec_model(data) or is_pydantic_model(data)) and operation == "create" and data.slug is None:  # type: ignore[union-attr]
            data.slug = await self.repository.get_available_slug(data.name)  # type: ignore[union-attr]
        if (is_msgspec_model(data) or is_pydantic_model(data)) and operation == "update" and data.slug is None:  # type: ignore[union-attr]
            data.slug = await self.repository.get_available_slug(data.name)  # type: ignore[union-attr]
        if is_dict(data) and "slug" not in data and operation == "create":
            data["slug"] = await self.repository.get_available_slug(data["name"])
        if is_dict(data) and "slug" not in data and "name" in data and operation == "update":
            data["slug"] = await self.repository.get_available_slug(data["name"])
        return await super().to_model(data, operation)


class UserRoleService(SQLAlchemyAsyncRepositoryService[UserRole]):
    """Handles database operations for user roles."""

    repository_type = UserRoleRepository

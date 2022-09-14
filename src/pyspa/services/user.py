from typing import TYPE_CHECKING, Optional

from sqlalchemy import orm, select

from pyspa import models, repositories, schemas
from pyspa.core import security
from pyspa.services.base import DataAccessService, DataAccessServiceException

if TYPE_CHECKING:
    from pydantic import UUID4, SecretStr
    from sqlalchemy.ext.asyncio import AsyncSession


class UserServiceException(DataAccessServiceException):
    """_summary_"""


class UserNotFoundException(UserServiceException):
    """_summary_"""


class UserLoginFailedException(UserServiceException):
    """_summary_"""


class UserInactiveException(UserServiceException):
    """_summary_"""


class UserPasswordVerifyException(UserServiceException):
    """_summary_"""


class UserService(DataAccessService[models.User, repositories.UserRepository, schemas.UserCreate, schemas.UserUpdate]):
    """Handles database operations for users"""

    async def exists(self, db: "AsyncSession", username: str) -> bool:
        statement = select(self.model.id).where(self.model.email == username)
        return await self.repository.get_one_or_none(db, statement) is not None

    async def authenticate(self, db: "AsyncSession", username: str, password: "SecretStr") -> models.User:
        """Authenticates a user

        Args:
            db: Database session
            username: User email
            password: password
        Returns:
            User object
        """
        user_obj = await self.repository.get_by_email(db, email=username)
        if user_obj is None:
            raise UserNotFoundException
        if not await security.verify_password(password, user_obj.hashed_password):
            raise UserLoginFailedException
        if not user_obj.is_active:
            raise UserInactiveException
        return user_obj

    async def update_password(
        self, db: "AsyncSession", obj_in: "schemas.UserPasswordUpdate", db_obj: "models.User"
    ) -> None:
        if not await security.verify_password(obj_in.current_password, db_obj.hashed_password):
            raise UserPasswordVerifyException
        if not self.is_active(db_obj):
            raise UserInactiveException
        db_obj.hashed_password = await security.get_password_hash(obj_in.new_password)
        await self.repository.update(db, db_obj)

    async def get_by_username(self, db: "AsyncSession", username: str) -> "Optional[models.User]":
        """Find a user by their email

        Args:
            db: Database session
            email: User email

        Returns:
            User object
        """
        db_obj = await self.repository.get_by_email(email=username, db=db)
        return db_obj or None

    @staticmethod
    def is_verified(db_obj: "models.User") -> bool:
        """Returns true if the user is verified"""
        return db_obj.is_verified

    @staticmethod
    def is_active(db_obj: "models.User") -> bool:
        """Returns true if the user is active"""
        return db_obj.is_active

    @staticmethod
    def is_superuser(db_obj: "models.User") -> bool:
        """Returns true if the user is a superuser"""
        return db_obj.is_superuser

    @staticmethod
    def is_workspace_member(db_obj: "models.User", workspace_id: "UUID4") -> bool:
        """Returns true if the user is a member of the workspace"""
        return any(membership.workspace.id == workspace_id for membership in db_obj.workspaces)

    @staticmethod
    def is_workspace_admin(db_obj: "models.User", workspace_id: "UUID4") -> bool:
        """Returns true if the user is an admin of the workspace"""
        return any(
            membership.workspace.id == workspace_id and membership.role == models.WorkspaceRoleTypes.ADMIN
            for membership in db_obj.workspaces
        )


user = UserService(
    model=models.User,
    repository=repositories.UserRepository,
    default_options=[
        orm.subqueryload(models.User.workspaces).options(
            orm.joinedload(models.WorkspaceMember.workspace, innerjoin=True).options(
                orm.noload("*"),
            ),
        ),
    ],
)

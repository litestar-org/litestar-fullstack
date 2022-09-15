from typing import TYPE_CHECKING, Optional

from sqlalchemy import orm, select
from sqlalchemy.ext.asyncio import AsyncSession

from pyspa import models, repositories, schemas
from pyspa.core import security
from pyspa.services.base import DataAccessService, DataAccessServiceException

if TYPE_CHECKING:
    from pydantic import UUID4, SecretStr


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

    async def exists(self, db: AsyncSession, username: str) -> bool:
        statement = select(self.model.id).where(self.model.email == username)
        return await self.repository.get_one_or_none(db, statement) is not None

    async def authenticate(self, db: AsyncSession, username: str, password: "SecretStr") -> models.User:
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
        self, db: AsyncSession, obj_in: "schemas.UserPasswordUpdate", db_obj: "models.User"
    ) -> None:
        if not await security.verify_password(obj_in.current_password, db_obj.hashed_password):
            raise UserPasswordVerifyException
        if not self.is_active(db_obj):
            raise UserInactiveException
        db_obj.hashed_password = await security.get_password_hash(obj_in.new_password)
        await self.repository.update(db, db_obj)

    async def get_by_username(self, db: AsyncSession, username: str) -> "Optional[models.User]":
        """Find a user by their email

        Args:
            db: Database session
            email: User email

        Returns:
            User object
        """
        db_obj = await self.repository.get_by_email(email=username, db=db)
        return db_obj or None

    async def create(self, db: AsyncSession, obj_in: schemas.UserCreate | schemas.UserSignup) -> models.User:
        obj_data = obj_in.dict(exclude_unset=True, exclude_none=True)
        password = obj_data.pop("password")
        invitation_id = obj_data.pop("invitation_id")
        team_name = obj_data.pop("team_name")
        obj_data.update({"hashed_password": security.get_password_hash(password)})
        user = models.User.from_dict(**obj_data)

        if team_name:
            """Create the team the user entered into the form"""
            team = models.Team(name=team_name)
            team.members.append(models.TeamMember(user=user, role=models.TeamRoleTypes.ADMIN, is_owner=True))
            db.add(team)
        if invitation_id:
            # invitation_obj = await services.invite.get(id=obj_in.invitation_id, db=db)
            #   TODO
            raise NotImplementedError
        await self.repository.create(db, user)
        await self.repository.refresh(db, user)
        return user

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
    def is_team_member(db_obj: "models.User", team_id: "UUID4") -> bool:
        """Returns true if the user is a member of the team"""
        return any(membership.team.id == team_id for membership in db_obj.teams)

    @staticmethod
    def is_team_admin(db_obj: "models.User", team_id: "UUID4") -> bool:
        """Returns true if the user is an admin of the team"""
        return any(
            membership.team.id == team_id and membership.role == models.TeamRoleTypes.ADMIN
            for membership in db_obj.teams
        )


user = UserService(
    model=models.User,
    repository=repositories.UserRepository,
    default_options=[
        orm.subqueryload(models.User.teams).options(
            orm.joinedload(models.TeamMember.team, innerjoin=True).options(
                orm.noload("*"),
            ),
        ),
    ],
)

from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import orm, select
from starlite import NotAuthorizedException

from app import schemas
from app.core import security
from app.core.db import models, repositories
from app.core.db.repositories.team import TeamRepository
from app.services.base import BaseRepositoryService, BaseRepositoryServiceException
from app.services.team_invite import (
    TeamInvitationEmailMismatchException,
    TeamInvitationExpired,
    TeamInvitationNotFoundException,
    team_invite,
)

if TYPE_CHECKING:
    from pydantic import UUID4, SecretStr
    from sqlalchemy.ext.asyncio import AsyncSession


class UserServiceException(BaseRepositoryServiceException):
    """_summary_"""


class UserNotFoundException(UserServiceException):
    """_summary_"""


class UserService(
    BaseRepositoryService[models.User, repositories.UserRepository, schemas.UserCreate, schemas.UserUpdate]
):
    """Handles database operations for users"""

    model_type = models.User
    repository_type = repositories.UserRepository

    async def exists(self, db_session: "AsyncSession", username: str) -> bool:
        statement = select(self.model.id).where(self.model.email == username)
        return await self.repository.get_one_or_none(db_session, statement) is not None

    async def authenticate(self, db_session: "AsyncSession", username: str, password: "SecretStr") -> models.User:
        """Authenticates a user

        Args:
            db_session:   Database session
            username: User email
            password: password
        Returns:
            User object
        """
        user_obj = await self.get_by_email(db_session, email=username)
        if user_obj is None:
            raise NotAuthorizedException("User not found or password invalid")
        if not await security.verify_password(password, user_obj.hashed_password):
            raise NotAuthorizedException("User not found or password invalid")
        if not user_obj.is_active:
            raise NotAuthorizedException("User account is inactive")
        return user_obj

    async def update_password(
        self, db_session: "AsyncSession", obj_in: schemas.UserPasswordUpdate, db_obj: models.User
    ) -> None:
        if not await security.verify_password(obj_in.current_password, db_obj.hashed_password):
            raise NotAuthorizedException("Password failed to match")
        if not self.is_active(db_obj):
            raise NotAuthorizedException("User account is not active")
        db_obj.hashed_password = await security.get_password_hash(obj_in.new_password)
        await self.repository.update(db_session, db_obj)

    async def get_by_username(
        self, db_session: "AsyncSession", username: str, options: Optional[list[Any]] = None
    ) -> Optional[models.User]:
        """Find a user by their email

        Args:
            db_session:   Database session
            email: User email

        Returns:
            User object
        """
        options = options if options else self.default_options
        statement = select(self.model).where(self.model.email == username).options(*options)
        return await self.repository.get_one_or_none(db_session, statement)

    async def get_by_email(
        self, db_session: "AsyncSession", email: str, options: Optional[list[Any]] = None
    ) -> models.User | None:
        options = options if options else self.default_options
        statement = select(self.model).where(self.model.email == email).options(*options)
        return await self.repository.get_one_or_none(db_session, statement)

    async def create(self, db_session: "AsyncSession", obj_in: schemas.UserCreate | schemas.UserSignup) -> models.User:
        obj_data = obj_in.dict(exclude_unset=True, exclude_none=True)
        password: "SecretStr" = obj_data.pop("password")
        invitation_id: UUID4 | None = obj_data.pop("invitation_id", None)
        team_name: str | None = obj_data.pop("team_name", None)
        obj_data.update({"hashed_password": await security.get_password_hash(password)})
        user = self.model(**obj_data)
        if team_name:
            """Create the team the user entered into the form"""
            slug = await TeamRepository().get_available_slug(db_session, team_name)
            team = models.Team(name=team_name, slug=slug)

            team.members.append(models.TeamMember(user=user, role=models.TeamRoles.ADMIN, is_owner=True))
            db_session.add(team)  # this will get committed with the user object below
        if invitation_id:
            invite = await team_invite.get_by_id(id=invitation_id, db_session=db_session)
            if not invite:
                raise TeamInvitationNotFoundException
            if invite.is_accepted:
                raise TeamInvitationExpired
            if invite.email != obj_in.email:
                raise TeamInvitationEmailMismatchException
            team.members.append(models.TeamMember(user=user, role=invite.role, is_owner=False))
            invite.is_accepted = True
            db_session.add(invite)  # this is automatically committed with the statement below
        user = await self.repository.create(db_session, user)
        return user

    @staticmethod
    def is_verified(db_obj: models.User) -> bool:
        """Returns true if the user is verified"""
        return db_obj.is_verified

    @staticmethod
    def is_active(db_obj: models.User) -> bool:
        """Returns true if the user is active"""
        return db_obj.is_active

    @staticmethod
    def is_superuser(db_obj: models.User) -> bool:
        """Returns true if the user is a superuser"""
        return db_obj.is_superuser

    @staticmethod
    def is_team_member(db_obj: models.User, team_id: "UUID4") -> bool:
        """Returns true if the user is a member of the team"""
        return any(membership.team.id == team_id for membership in db_obj.teams)

    @staticmethod
    def is_team_admin(db_obj: models.User, team_id: "UUID4") -> bool:
        """Returns true if the user is an admin of the team"""
        return any(
            membership.team.id == team_id and membership.role == models.TeamRoles.ADMIN for membership in db_obj.teams
        )

    @staticmethod
    def is_team_owner(db_obj: models.User, team_id: "UUID4") -> bool:
        """Returns true if the user is an admin of the team"""
        return any(membership.team.id == team_id and membership.is_owner for membership in db_obj.teams)


user = UserService(
    default_options=[
        orm.subqueryload(models.User.teams).options(
            orm.joinedload(models.TeamMember.team, innerjoin=True).options(
                orm.noload("*"),
            ),
        ),
    ],
)

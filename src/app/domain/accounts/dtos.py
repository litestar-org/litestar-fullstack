import msgspec
from advanced_alchemy.extensions.litestar.dto import SQLAlchemyDTO

from app.db.models import User
from app.lib import dto

__all__ = (
    "AccountLogin",
    "AccountRegister",
    "UserRoleAdd",
    "UserRoleRevoke",
    "UserCreate",
    "UserDTO",
    "UserUpdate",
)


# database model


class UserDTO(SQLAlchemyDTO[User]):
    config = dto.config(
        backend="sqlalchemy",
        exclude={
            "oauth_accounts",
            "hashed_password",
            "teams.team",
            "teams.user",
            "teams.created_at",
            "teams.updated_at",
            "teams.id",
            "teams.user_name",
            "teams.user_email",
        },
        max_nested_depth=1,
    )


# input


class UserCreate(msgspec.Struct):
    email: str
    password: str
    name: str | None = None
    is_superuser: bool = False
    is_active: bool = True
    is_verified: bool = False


class UserUpdate(msgspec.Struct):
    email: str | None = None
    password: str | None = None
    name: str | None = None
    is_superuser: bool | None = None
    is_active: bool | None = None
    is_verified: bool | None = None


class AccountLogin(msgspec.Struct):
    username: str
    password: str


class AccountRegister(msgspec.Struct):
    email: str
    password: str
    name: str | None = None


class UserRoleAdd(msgspec.Struct):
    """User role add ."""

    user_name: str


class UserRoleRevoke(msgspec.Struct):
    """User role revoke ."""

    user_name: str

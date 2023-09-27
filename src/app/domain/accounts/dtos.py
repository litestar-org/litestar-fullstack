from dataclasses import dataclass

from advanced_alchemy.extensions.litestar.dto import SQLAlchemyDTO
from litestar.dto import DataclassDTO

from app.domain.accounts.models import User
from app.lib import dto

__all__ = [
    "AccountLogin",
    "AccountLoginDTO",
    "AccountRegister",
    "AccountRegisterDTO",
    "UserCreate",
    "UserCreateDTO",
    "UserDTO",
    "UserUpdate",
    "UserUpdateDTO",
]


# database model


class UserDTO(SQLAlchemyDTO[User]):
    config = dto.config(
        exclude={
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


@dataclass
class UserCreate:
    email: str
    password: str
    name: str | None = None
    is_superuser: bool = False
    is_active: bool = True
    is_verified: bool = False


class UserCreateDTO(DataclassDTO[UserCreate]):
    """User Create."""

    config = dto.config()


@dataclass
class UserUpdate:
    email: str | None = None
    password: str | None = None
    name: str | None = None
    is_superuser: bool | None = None
    is_active: bool | None = None
    is_verified: bool | None = None


class UserUpdateDTO(DataclassDTO[UserUpdate]):
    """User Update."""

    config = dto.config()


@dataclass
class AccountLogin:
    username: str
    password: str


class AccountLoginDTO(DataclassDTO[AccountLogin]):
    """User Login."""

    config = dto.config()


@dataclass
class AccountRegister:
    email: str
    password: str
    name: str | None = None


class AccountRegisterDTO(DataclassDTO[AccountRegister]):
    """User Account Registration."""

    config = dto.config()

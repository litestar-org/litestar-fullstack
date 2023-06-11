from dataclasses import dataclass

from litestar.contrib.sqlalchemy.dto import SQLAlchemyDTO
from litestar.dto.factory.stdlib.dataclass import DataclassDTO

from app.domain.accounts.models import User
from app.lib import dto

# database model


class UserDTO(SQLAlchemyDTO[User]):
    config = dto.config(
        exclude={
            "hashed_password",
            "teams.team",
            "teams.user",
            "teams.created",
            "teams.updated",
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
    email: str
    password: str
    name: str
    is_superuser: bool
    is_active: bool
    is_verified: bool


class UserUpdateDTO(DataclassDTO[UserUpdate]):
    """User Update."""

    config = dto.config(partial=True)


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

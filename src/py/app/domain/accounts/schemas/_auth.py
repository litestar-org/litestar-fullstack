"""Authentication-related schemas."""

import msgspec

from app.lib.schema import CamelizedBaseStruct
from app.lib.validation import validate_email, validate_name, validate_password, validate_username


class AccountLogin(CamelizedBaseStruct):
    username: str
    password: str

    def __post_init__(self) -> None:
        """Validate email format for username."""
        self.username = validate_email(self.username)


class AccountRegister(CamelizedBaseStruct):
    email: str
    password: str
    name: str | None = None
    username: str | None = None
    initial_team_name: str | msgspec.UnsetType | None = msgspec.UNSET

    def __post_init__(self) -> None:
        """Validate fields."""
        self.email = validate_email(self.email)
        self.password = validate_password(self.password)
        if self.name is not None:
            self.name = validate_name(self.name)
        if self.username is not None:
            self.username = validate_username(self.username)


class PasswordUpdate(CamelizedBaseStruct):
    current_password: str
    new_password: str

    def __post_init__(self) -> None:
        """Validate new password strength."""
        self.new_password = validate_password(self.new_password)


class PasswordVerify(CamelizedBaseStruct):
    current_password: str

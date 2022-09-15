import base64
import logging
from typing import TYPE_CHECKING

from passlib.context import CryptContext

from pyspa import db, services
from pyspa.config import paths, settings
from pyspa.middleware import OAuth2PasswordBearerAuth
from pyspa.utils.asyncer import run_async

if TYPE_CHECKING:
    from pydantic import SecretStr

    from pyspa.models import User

logger = logging.getLogger()


class SecurityException(Exception):
    """Base exception for security"""


class UserInactiveException(SecurityException):
    """Inactive User"""


class AuthenticationInvalidException(SecurityException):
    """Inactive User"""


class AccessForbiddenException(SecurityException):
    """Not enough permissions"""


async def current_user(sub: str) -> "User":
    user = await services.user.get_by_username(db.db_session(), sub)
    if user:
        return user
    raise AccessForbiddenException


oauth2_authentication = OAuth2PasswordBearerAuth(  # nosec
    retrieve_user_handler=current_user,
    token_secret=settings.app.SECRET_KEY.get_secret_value(),
    token_url=paths.urls.ACCESS_TOKEN,
    exclude=[paths.urls.OPENAPI_SCHEMA, paths.urls.HEALTH, paths.urls.ACCESS_TOKEN, paths.urls.SIGNUP],
)

password_crypt_context = CryptContext(schemes=["argon2"], deprecated="auto")


def get_encryption_key(secret: str) -> bytes:
    padded_secret = f"{secret:<32}"[0:32]
    return base64.urlsafe_b64encode(padded_secret.encode())


async def get_password_hash(password: "SecretStr") -> str:
    """Get password hash
    Args:
        password: Plain password
    Returns:
        Hashed password
    """
    pw_hash = await run_async(password_crypt_context.hash)(password.get_secret_value())
    return pw_hash


async def verify_password(plain_password: "SecretStr", hashed_password: str) -> bool:
    """Verify password
    Args:
        plain_password: Plain password
        hashed_password: Hashed password
    Returns:
        True if password is correct
    """
    valid, _ = await run_async(password_crypt_context.verify_and_update)(
        plain_password.get_secret_value(),
        hashed_password,
    )
    return bool(valid)

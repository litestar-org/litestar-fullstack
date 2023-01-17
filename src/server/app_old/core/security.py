import base64
import logging
from typing import TYPE_CHECKING, Any, Union

from app import services
from app.config import paths, settings
from app.utils.asyncer import run_async
from passlib.context import CryptContext
from starlite import ASGIConnection, NotAuthorizedException
from starlite.contrib.jwt.jwt_auth import OAuth2PasswordBearerAuth

if TYPE_CHECKING:
    from app.core.db.models import User
    from pydantic import SecretBytes, SecretStr

logger = logging.getLogger()


async def current_user_from_token(token: str, connection: ASGIConnection[Any, Any, Any]) -> "User":
    """Current user from local JWT token.

    Fetches the user information from the database when loading from a local token.

    If the user doesn't exist, the record will be created and returned.

    Args:
        unique_identifier (str): _description_
        connection (ASGIConnection[Any, Any, Any]): ASGI connection.

    Raises:
        NotAuthorizedException: User not authorized.

    Returns:
        User: User record mapped to the JWT identifier
    """
    async with sqlalchemy_plugin.async_session_factory() as db_session:
        user = await services.users.get_by_email(db_session, token.sub)
        if user and user.is_active:
            return user
    raise NotAuthorizedException("Unable to validate token.")


auth = OAuth2PasswordBearerAuth(  # nosec
    retrieve_user_handler=current_user_from_token,
    token_secret=settings.app.SECRET_KEY.get_secret_value().decode(),
    token_url=paths.urls.ACCESS_TOKEN,
    exclude=[
        paths.urls.OPENAPI_SCHEMA,
        paths.urls.HEALTH,
        paths.urls.ACCESS_TOKEN,
        paths.urls.SIGNUP,
        paths.urls.STATIC,
        paths.urls.INDEX,
    ],
)

password_crypt_context = CryptContext(schemes=["argon2"], deprecated="auto")


def get_encryption_key(secret: str) -> bytes:
    padded_secret = f"{secret:<32}"[0:32]
    return base64.urlsafe_b64encode(padded_secret.encode())


async def get_password_hash(password: Union["SecretBytes", "SecretStr"]) -> str:
    """Get password hash
    Args:
        password: Plain password
    Returns:
        Hashed password.
    """
    pw_hash = await run_async(password_crypt_context.hash)(password.get_secret_value())
    return pw_hash


async def verify_password(plain_password: Union["SecretBytes", "SecretStr"], hashed_password: str) -> bool:
    """Verify password
    Args:
        plain_password: Plain password
        hashed_password: Hashed password
    Returns:
        True if password is correct.
    """
    valid, _ = await run_async(password_crypt_context.verify_and_update)(
        plain_password.get_secret_value(),
        hashed_password,
    )
    return bool(valid)

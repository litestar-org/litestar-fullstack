from __future__ import annotations

import base64
import logging
from typing import TYPE_CHECKING

from passlib.context import CryptContext
from starlite.utils.sync import AsyncCallable

if TYPE_CHECKING:
    from pydantic import SecretBytes, SecretStr

logger = logging.getLogger()


password_crypt_context = CryptContext(schemes=["argon2"], deprecated="auto")


def get_encryption_key(secret: str) -> bytes:
    """Get Encryption Key.

    Args:
        secret (str): Secret key used for encryption

    Returns:
        bytes: a URL safe encoded version of secret
    """
    padded_secret = f"{secret:<32}"[0:32]
    return base64.urlsafe_b64encode(padded_secret.encode())


async def get_password_hash(password: SecretBytes | SecretStr) -> str:
    """Get password hash.

    Args:
        password: Plain password
    Returns:
        str: Hashed password
    """
    return await AsyncCallable(password_crypt_context.hash)(secret=password.get_secret_value())


async def verify_password(plain_password: SecretBytes | SecretStr, hashed_password: str) -> bool:
    """Verify Password.

    Args:
        plain_password (SecretBytes | SecretStr): Password input
        hashed_password (str): Password hash to verify against

    Returns:
        bool: True if the password hashes match
    """
    valid, _ = await AsyncCallable(password_crypt_context.verify_and_update)(
        secret=plain_password.get_secret_value(),
        hash=hashed_password,
    )
    return bool(valid)

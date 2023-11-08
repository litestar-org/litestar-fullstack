from __future__ import annotations

import asyncio
import base64
import logging

from passlib.context import CryptContext
from pydantic import SecretBytes, SecretStr

__all__ = ["get_encryption_key", "get_password_hash", "verify_password"]


logger = logging.getLogger()


password_crypt_context = CryptContext(schemes=["argon2"], deprecated="auto")


def get_encryption_key(secret: str) -> bytes:
    """Get Encryption Key.

    Args:
        secret (str): Secret key used for encryption

    Returns:
        bytes: a URL safe encoded version of secret
    """
    if len(secret) <= 32:
        secret = f"{secret:<32}"[:32]
    return base64.urlsafe_b64encode(secret.encode())


async def get_password_hash(password: SecretBytes | SecretStr | str | bytes) -> str:
    """Get password hash.

    Args:
        password: Plain password
    Returns:
        str: Hashed password
    """
    if isinstance(password, SecretBytes | SecretStr):
        password = password.get_secret_value()
    return await asyncio.get_running_loop().run_in_executor(None, password_crypt_context.hash, password)


async def verify_password(plain_password: SecretBytes | SecretStr | str | bytes, hashed_password: str) -> bool:
    """Verify Password.

    Args:
        plain_password (SecretBytes | SecretStr): _description_
        hashed_password (str): _description_

    Returns:
        bool: _description_
    """
    if isinstance(plain_password, SecretBytes | SecretStr):
        plain_password = plain_password.get_secret_value()
    valid, _ = await asyncio.get_running_loop().run_in_executor(
        None,
        password_crypt_context.verify_and_update,
        plain_password,
        hashed_password,
    )
    return bool(valid)

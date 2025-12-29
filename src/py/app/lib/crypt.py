from __future__ import annotations

import asyncio
import base64
import importlib
import secrets
from io import BytesIO
from typing import TYPE_CHECKING, Any, Literal, cast, overload

import pyotp
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

qrcode: Any = importlib.import_module("qrcode")

if TYPE_CHECKING:
    from PIL.Image import Image

hasher = PasswordHash((Argon2Hasher(),))


def get_encryption_key(secret: str) -> bytes:
    """Get Encryption Key.

    Args:
        secret (str): Secret key used for encryption

    Returns:
        bytes: a URL safe encoded version of secret
    """
    if len(secret) <= 32:  # noqa: PLR2004
        secret = f"{secret:<32}"[:32]
    return base64.urlsafe_b64encode(secret.encode())


async def get_password_hash(password: str | bytes) -> str:
    """Get password hash.

    Args:
        password: Plain password

    Returns:
        str: Hashed password
    """
    return await asyncio.get_running_loop().run_in_executor(None, hasher.hash, password)


async def verify_password(plain_password: str | bytes, hashed_password: str) -> bool:
    """Verify Password.

    Args:
        plain_password (str | bytes): The string or byte password
        hashed_password (str): the hash of the password

    Returns:
        bool: True if password matches hash.
    """
    valid, _ = await asyncio.get_running_loop().run_in_executor(
        None,
        hasher.verify_and_update,
        plain_password,
        hashed_password,
    )
    return bool(valid)


# TOTP/MFA Functions


def generate_totp_secret() -> str:
    """Generate a new TOTP secret.

    Returns:
        A base32-encoded secret key for TOTP.
    """
    return pyotp.random_base32()


def verify_totp_code(secret: str, code: str) -> bool:
    """Verify a TOTP code.

    Args:
        secret: The user's TOTP secret.
        code: The 6-digit code to verify.

    Returns:
        True if the code is valid, False otherwise.
    """
    totp = pyotp.TOTP(secret)
    return totp.verify(code, valid_window=1)  # Allow 30 second window


def get_totp_provisioning_uri(secret: str, email: str, issuer: str = "Litestar App") -> str:
    """Get the provisioning URI for TOTP setup.

    Args:
        secret: The TOTP secret.
        email: The user's email address.
        issuer: The application name.

    Returns:
        The otpauth:// URI for the authenticator app.
    """
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=email, issuer_name=issuer)


def generate_totp_qr_code(secret: str, email: str, issuer: str = "Litestar App") -> bytes:
    """Generate a QR code image for TOTP setup.

    Args:
        secret: The TOTP secret.
        email: The user's email address.
        issuer: The application name.

    Returns:
        PNG image data as bytes.
    """
    uri = get_totp_provisioning_uri(secret, email, issuer)
    img = cast("Image", qrcode.make(uri))
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer.getvalue()


def generate_backup_codes(count: int = 8) -> list[str]:
    """Generate recovery backup codes.

    Args:
        count: Number of backup codes to generate.

    Returns:
        List of backup codes (plaintext).
    """
    return [secrets.token_hex(4).upper() for _ in range(count)]


async def hash_backup_codes(codes: list[str]) -> list[str]:
    """Hash backup codes for storage.

    Args:
        codes: List of plaintext backup codes.

    Returns:
        List of hashed backup codes.
    """
    return [await get_password_hash(code) for code in codes]


@overload
async def verify_backup_code(
    code: str,
    hashed_codes: list[str | None],
    *,
    raise_on_not_found: Literal[True],
) -> int: ...


@overload
async def verify_backup_code(
    code: str,
    hashed_codes: list[str | None],
    *,
    raise_on_not_found: Literal[False] = ...,
) -> int | None: ...


async def verify_backup_code(
    code: str,
    hashed_codes: list[str | None],
    *,
    raise_on_not_found: bool = False,
) -> int | None:
    """Verify a backup code against the stored hashes.

    Args:
        code: The plaintext backup code to verify.
        hashed_codes: List of hashed backup codes (None entries are skipped).
        raise_on_not_found: If True, raise ValueError when code is not found.

    Returns:
        The index of the matching code if found, None otherwise (unless raise_on_not_found is True).

    Raises:
        ValueError: If raise_on_not_found is True and the code is not found.
    """
    for i, hashed in enumerate(hashed_codes):
        if hashed is not None and await verify_password(code, hashed):
            return i
    if raise_on_not_found:
        raise ValueError("Invalid backup code")
    return None

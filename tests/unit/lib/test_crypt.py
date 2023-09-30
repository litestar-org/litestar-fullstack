# pylint: disable=protected-access
from __future__ import annotations

import base64

import pytest
from pydantic import SecretBytes, SecretStr

from app.lib import crypt


@pytest.mark.parametrize(
    ("secret_key", "expected_value"),
    (
        ("test", "test                            "),
        ("test---------------------------", "test--------------------------- "),
        ("test----------------------------", "test----------------------------"),
        ("test-----------------------------", "test-----------------------------"),
        (
            "this is a really long string that exceeds the 32 character padding added.",
            "this is a really long string that exceeds the 32 character padding added.",
        ),
    ),
)
async def test_get_encryption_key(secret_key: str, expected_value: str) -> None:
    """Test that the encryption key is formatted correctly."""
    secret = crypt.get_encryption_key(secret_key)
    decoded = base64.urlsafe_b64decode(secret)
    assert expected_value == decoded.decode()


async def test_get_password_hash() -> None:
    """Test that the encryption key is formatted correctly."""
    secret_str = SecretStr("This is a password!")
    secret_bytes = SecretBytes(b"This is a password too!")
    secret_str_hash = await crypt.get_password_hash(secret_str)
    secret_bytes_hash = await crypt.get_password_hash(secret_bytes)

    assert secret_str_hash.startswith("$argon2")
    assert secret_bytes_hash.startswith("$argon2")


@pytest.mark.parametrize(
    ("valid_password", "tested_password", "expected_result"),
    (("SuperS3cret123456789!!", "SuperS3cret123456789!!", True), ("SuperS3cret123456789!!", "Invalid!!", False)),
)
async def test_verify_password(valid_password: str, tested_password: str, expected_result: bool) -> None:
    """Test that the encryption key is formatted correctly."""

    secret_str_hash = await crypt.get_password_hash(valid_password)
    is_valid = await crypt.verify_password(tested_password, secret_str_hash)

    assert is_valid == expected_result

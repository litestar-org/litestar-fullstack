import pyotp
import pytest

from app.lib import crypt

pytestmark = pytest.mark.anyio


async def test_password_hashing() -> None:
    password = "secret-password"
    hashed = await crypt.get_password_hash(password)
    assert hashed != password
    assert await crypt.verify_password(password, hashed) is True
    assert await crypt.verify_password("wrong-password", hashed) is False


def test_encryption_key() -> None:
    key = crypt.get_encryption_key("short")
    assert len(key) >= 32

    key2 = crypt.get_encryption_key("a" * 40)
    assert len(key2) >= 32


def test_totp_flow() -> None:
    secret = crypt.generate_totp_secret()
    assert len(secret) == 32

    uri = crypt.get_totp_provisioning_uri(secret, "user@example.com", "App")
    assert "otpauth://totp/App:user%40example.com" in uri
    assert "secret=" + secret in uri

    totp = pyotp.TOTP(secret)
    code = totp.now()
    assert crypt.verify_totp_code(secret, code) is True
    assert crypt.verify_totp_code(secret, "000000") is False


async def test_generate_totp_qr_code() -> None:
    secret = crypt.generate_totp_secret()
    qr_bytes = await crypt.generate_totp_qr_code(secret, "user@example.com")
    assert isinstance(qr_bytes, bytes)
    assert len(qr_bytes) > 0
    # PNG header
    assert qr_bytes.startswith(b"\x89PNG")


def test_backup_codes() -> None:
    codes = crypt.generate_backup_codes(5)
    assert len(codes) == 5
    for code in codes:
        assert len(code) == 8  # token_hex(4) is 8 chars


async def test_verify_backup_code() -> None:
    codes = ["CODE1", "CODE2"]

    hashed_codes: list[str | None] = [await crypt.get_password_hash(c) for c in codes]

    idx = await crypt.verify_backup_code("CODE2", hashed_codes)

    assert idx == 1

    idx = await crypt.verify_backup_code("WRONG", hashed_codes)
    assert idx is None

    with pytest.raises(ValueError, match="Invalid backup code"):
        await crypt.verify_backup_code("WRONG", hashed_codes, raise_on_not_found=True)

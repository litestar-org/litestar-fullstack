from __future__ import annotations

import pyotp

from app.lib.crypt import generate_totp_secret, verify_totp_code


def test_totp_roundtrip() -> None:
    secret = generate_totp_secret()
    code = pyotp.TOTP(secret).now()
    assert verify_totp_code(secret, code)

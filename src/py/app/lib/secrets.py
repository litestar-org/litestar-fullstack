"""Purpose-isolated HKDF-SHA256 subkey derivation for application subsystems."""

from __future__ import annotations

from typing import Final

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

SESSION_COOKIE_SECRET_INFO: Final[bytes] = b"app.auth.session-cookie-secret.v1"
PURPOSE_TOKEN_PEPPER_INFO: Final[bytes] = b"app.auth.purpose-token-pepper.v1"
RECOVERY_CODE_PEPPER_INFO: Final[bytes] = b"app.auth.recovery-code-pepper.v1"
TOTP_PROTECTOR_INFO: Final[bytes] = b"app.auth.totp-protector.v1"
OAUTH_PROTECTOR_INFO: Final[bytes] = b"app.auth.oauth-protector.v1"
OAUTH_TRANSACTION_PEPPER_INFO: Final[bytes] = b"app.auth.oauth-transaction-pepper.v1"
SESSION_BINDING_PEPPER_INFO: Final[bytes] = b"app.auth.session-binding-pepper.v1"
API_KEY_PEPPER_INFO: Final[bytes] = b"app.auth.api-key-pepper.v1"
CSRF_SECRET_INFO: Final[bytes] = b"app.auth.csrf-secret.v1"
CURSOR_SECRET_INFO: Final[bytes] = b"app.db.cursor-secret.v1"

MIN_SUBKEY_LENGTH: Final[int] = 16

__all__ = (
    "API_KEY_PEPPER_INFO",
    "CSRF_SECRET_INFO",
    "CURSOR_SECRET_INFO",
    "MIN_SUBKEY_LENGTH",
    "OAUTH_PROTECTOR_INFO",
    "OAUTH_TRANSACTION_PEPPER_INFO",
    "PURPOSE_TOKEN_PEPPER_INFO",
    "RECOVERY_CODE_PEPPER_INFO",
    "SESSION_BINDING_PEPPER_INFO",
    "SESSION_COOKIE_SECRET_INFO",
    "TOTP_PROTECTOR_INFO",
    "derive_subkey",
)


def derive_subkey(master_secret: str, info: bytes, *, length: int = 32) -> bytes:
    """Derive a purpose-isolated subkey from the application master secret using HKDF-SHA256.

    Args:
        master_secret: Non-empty application master secret string.
        info: Non-empty domain-separation info label bytes.
        length: Output key length in bytes; must be at least 16.

    Returns:
        Deterministic derived subkey bytes of ``length`` bytes.

    Raises:
        ValueError: If ``master_secret`` is empty, ``info`` is empty, or ``length`` is below 16.
    """
    if not master_secret:
        msg = "master_secret must not be empty"
        raise ValueError(msg)
    if not info:
        msg = "info label must not be empty"
        raise ValueError(msg)
    if length < MIN_SUBKEY_LENGTH:
        msg = f"length must be at least {MIN_SUBKEY_LENGTH} bytes"
        raise ValueError(msg)

    kdf = HKDF(
        algorithm=hashes.SHA256(),
        length=length,
        salt=None,
        info=info,
    )
    return kdf.derive(master_secret.encode("utf-8"))

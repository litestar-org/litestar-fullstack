"""Session and token refresh schemas."""

from datetime import datetime
from uuid import UUID

import msgspec


class ActiveSession(msgspec.Struct, gc=False, array_like=True, omit_defaults=True, kw_only=True):
    """Information about an active session (refresh token)."""

    id: UUID
    created_at: datetime
    expires_at: datetime
    device_info: str | None = None
    is_current: bool = False


class SessionList(msgspec.Struct, gc=False, array_like=True, omit_defaults=True):
    """List of active user sessions."""

    sessions: list[ActiveSession]
    count: int


class TokenRefresh(msgspec.Struct, gc=False, array_like=True, omit_defaults=True):
    """Confirmation that token was refreshed."""

    message: str = "Token refreshed successfully"

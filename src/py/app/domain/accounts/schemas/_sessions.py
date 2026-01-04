"""Session and token refresh schemas."""

from datetime import datetime
from uuid import UUID

from app.lib.schema import CamelizedBaseStruct


class ActiveSession(CamelizedBaseStruct, kw_only=True):
    """Information about an active session (refresh token)."""

    id: UUID
    created_at: datetime
    expires_at: datetime
    device_info: str | None = None
    is_current: bool = False


class TokenRefresh(CamelizedBaseStruct):
    """Confirmation that token was refreshed."""

    message: str = "Token refreshed successfully"

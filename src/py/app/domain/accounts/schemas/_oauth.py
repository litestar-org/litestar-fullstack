"""OAuth-related schemas."""

from datetime import datetime

from app.lib.schema import CamelizedBaseStruct


class OAuthAuthorization(CamelizedBaseStruct):
    """OAuth authorization URL and state."""

    authorization_url: str
    state: str | None = None


class OAuthAccountInfo(CamelizedBaseStruct):
    """OAuth account information."""

    provider: str
    oauth_id: str
    email: str
    linked_at: datetime
    name: str | None = None
    avatar_url: str | None = None
    last_login_at: datetime | None = None

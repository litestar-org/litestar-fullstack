"""OAuth-related schemas."""

from datetime import datetime

import msgspec


class OAuthAuthorization(msgspec.Struct, gc=False, array_like=True, omit_defaults=True):
    """OAuth authorization URL and state."""

    authorization_url: str
    state: str | None = None


class OAuthAccountInfo(msgspec.Struct, gc=False, array_like=True, omit_defaults=True):
    """OAuth account information."""

    provider: str
    oauth_id: str
    email: str
    linked_at: datetime
    name: str | None = None
    avatar_url: str | None = None
    last_login_at: datetime | None = None

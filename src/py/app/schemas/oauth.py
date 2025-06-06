"""OAuth authentication schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

import msgspec


class OAuthAuthorizationRequest(msgspec.Struct, gc=False, array_like=True, omit_defaults=True):
    """OAuth authorization request payload."""

    provider: Literal["google"]
    redirect_url: str | None = None


class OAuthAuthorizationResponse(msgspec.Struct, gc=False, array_like=True, omit_defaults=True):
    """OAuth authorization response."""

    authorization_url: str
    state: str | None = None


class OAuthCallbackRequest(msgspec.Struct, gc=False, array_like=True, omit_defaults=True):
    """OAuth callback request."""

    code: str
    provider: Literal["google"]
    state: str | None = None


class OAuthLinkRequest(msgspec.Struct, gc=False, array_like=True, omit_defaults=True):
    """Request to link/unlink OAuth account."""

    provider: Literal["google"]


class OAuthAccountInfo(msgspec.Struct, gc=False, array_like=True, omit_defaults=True):
    """OAuth account information."""

    provider: str
    oauth_id: str
    email: str
    linked_at: datetime
    name: str | None = None
    avatar_url: str | None = None
    last_login_at: datetime | None = None

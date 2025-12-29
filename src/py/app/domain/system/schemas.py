"""System domain schemas."""

from __future__ import annotations

from typing import Literal

from app.__metadata__ import __version__
from app.schemas.base import CamelizedBaseStruct

__all__ = (
    "OAuthConfig",
    "SystemHealth",
)


class SystemHealth(CamelizedBaseStruct):
    app: str
    database_status: Literal["online", "offline"] = "offline"
    version: str = __version__


class OAuthConfig(CamelizedBaseStruct):
    """OAuth provider configuration for frontend."""

    google_enabled: bool = False
    github_enabled: bool = False

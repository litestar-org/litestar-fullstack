"""System domain schemas."""

from __future__ import annotations

from typing import Literal

from app.__metadata__ import __version__
from app.lib.settings import get_settings
from app.schemas.base import CamelizedBaseStruct

__all__ = (
    "OAuthConfig",
    "SystemHealth",
)

settings = get_settings()


class SystemHealth(CamelizedBaseStruct):
    database_status: Literal["online", "offline"] = "offline"
    app: str = settings.app.NAME
    version: str = __version__


class OAuthConfig(CamelizedBaseStruct):
    """OAuth provider configuration for frontend."""

    google_enabled: bool = False
    github_enabled: bool = False

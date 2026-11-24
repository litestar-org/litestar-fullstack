"""System health and public authentication configuration schemas."""

from __future__ import annotations

from typing import Literal

from app.__metadata__ import __version__
from app.lib.schema import CamelizedBaseStruct


class SystemHealth(CamelizedBaseStruct, kw_only=True):
    """Health status payload reporting database and queue backend availability."""

    app: str
    database_status: Literal["online", "offline"] = "offline"
    queue_status: Literal["online", "offline"] = "offline"
    version: str = __version__


class PublicAuthConfig(CamelizedBaseStruct, kw_only=True):
    """Public authentication capability flags exposed to browser clients."""

    google_enabled: bool = False
    github_enabled: bool = False
    passkeys_enabled: bool = True
    mfa_enabled: bool = True

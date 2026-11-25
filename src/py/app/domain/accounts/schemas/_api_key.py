"""API key management schemas."""

from __future__ import annotations

from datetime import datetime  # noqa: TC003

from app.lib.schema import CamelizedBaseStruct

__all__ = ("APIKeyCreate", "APIKeyIssued", "APIKeyItem")


class APIKeyCreate(CamelizedBaseStruct):
    """Request payload for minting a user-scoped API key."""

    name: str
    scopes: list[str] = []
    expires_in_days: int | None = None
    current_password: str | None = None

    def __post_init__(self) -> None:
        """Validate API key display name and optional expiration window.

        Raises:
            ValueError: If ``name`` is empty after stripping or ``expires_in_days`` is less than 1.
        """
        self.name = self.name.strip()
        if not self.name:
            msg = "API key name cannot be empty"
            raise ValueError(msg)
        if self.expires_in_days is not None and self.expires_in_days < 1:
            msg = "expires_in_days must be at least 1"
            raise ValueError(msg)


class APIKeyIssued(CamelizedBaseStruct):
    """Reveal-once response payload returned immediately upon API key issuance or rotation."""

    id: str
    name: str
    prefix: str
    secret: str
    scopes: list[str]
    created_at: datetime
    expires_at: datetime | None = None


class APIKeyItem(CamelizedBaseStruct):
    """Secret-free API key metadata returned by listing endpoints."""

    id: str
    name: str
    prefix: str
    scopes: list[str]
    created_at: datetime
    expires_at: datetime | None = None
    last_used_at: datetime | None = None
    revoked_at: datetime | None = None

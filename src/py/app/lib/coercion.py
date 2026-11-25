"""Coercions for timestamps and identifiers that cross a storage or protocol boundary."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

__all__ = ("ensure_utc", "parse_uuid")


def ensure_utc(value: datetime) -> datetime:
    """Return ``value`` as an aware UTC datetime, treating naive values as UTC.

    Returns:
        Timezone-aware UTC datetime.
    """
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def parse_uuid(raw: str | None) -> UUID | None:
    """Parse an account identifier, returning ``None`` for blank or malformed input.

    Returns:
        Parsed ``UUID``, or ``None`` when ``raw`` is not a UUID.
    """
    if not raw:
        return None
    try:
        return UUID(raw)
    except ValueError:
        return None

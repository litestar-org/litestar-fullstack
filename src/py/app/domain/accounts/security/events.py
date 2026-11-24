"""Audit-log sink persisting sanitized ``litestar-security`` ``SecurityEvent`` entries."""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, cast
from uuid import UUID

import structlog
from sqlalchemy.exc import SQLAlchemyError

from app.db import models as m

if TYPE_CHECKING:
    from advanced_alchemy.extensions.litestar import SQLAlchemyAsyncConfig
    from litestar_security.accounts import SecurityEvent

logger = structlog.get_logger(__name__)

_SENSITIVE_KEY_TOKENS = frozenset(
    {
        "password",
        "secret",
        "token",
        "recovery_code",
        "challenge",
        "api_key",
        "otp",
        "code",
        "digest",
        "verifier",
        "credential",
    }
)

__all__ = ("AuditSecurityEventSink", "sanitize_event_details")


def _is_sensitive_key(key: str) -> bool:
    lowered = key.lower()
    return any(marker in lowered for marker in _SENSITIVE_KEY_TOKENS)


def sanitize_event_details(payload: Any) -> Any:
    """Recursively redact sensitive keys from structured audit metadata."""
    if isinstance(payload, Mapping):
        mapping = cast("Mapping[object, object]", payload)
        sanitized: dict[str, Any] = {}
        for raw_key, value in mapping.items():
            key = str(raw_key)
            if _is_sensitive_key(key):
                sanitized[key] = "[REDACTED]"
            else:
                sanitized[key] = sanitize_event_details(value)
        return sanitized
    if isinstance(payload, list | tuple | set | frozenset):
        items = cast("list[object] | tuple[object, ...] | set[object] | frozenset[object]", payload)
        return [sanitize_event_details(item) for item in items]
    if isinstance(payload, bytes | bytearray):
        return "[REDACTED_BYTES]"
    return payload


def _parse_optional_uuid(raw: str | None) -> UUID | None:
    if not raw:
        return None
    try:
        return UUID(raw)
    except ValueError:
        return None


class AuditSecurityEventSink:
    """``SecurityEventSink`` writing redacted security telemetry to ``AuditLog``."""

    __slots__ = ("_alchemy_config", "_strict")

    def __init__(self, alchemy_config: SQLAlchemyAsyncConfig, *, strict: bool = False) -> None:
        """Initialize the audit event sink.

        Args:
            alchemy_config: Shared Advanced Alchemy async configuration.
            strict: Whether to re-raise database write errors instead of logging and suppressing.
        """
        self._alchemy_config = alchemy_config
        self._strict = strict

    async def emit(self, event: SecurityEvent) -> None:
        """Persist one sanitized ``SecurityEvent`` record into ``audit_log``."""
        raw_actor = event.principal_id or event.account_id
        actor_uuid = _parse_optional_uuid(raw_actor)
        correlation: dict[str, Any] = (
            cast("dict[str, Any]", sanitize_event_details(dict(event.correlation))) if event.correlation else {}
        )
        details: dict[str, Any] = {
            "event_id": event.event_id,
            "occurred_at": event.occurred_at.isoformat(),
            "outcome": event.outcome,
            "mechanism": event.mechanism,
            "session_id": event.session_id,
            "family_id": event.family_id,
            "correlation": correlation,
        }
        if raw_actor is not None and actor_uuid is None:
            details["raw_actor_id"] = raw_actor

        ip_address: Any = correlation.get("ip_address")
        user_agent: Any = correlation.get("user_agent")

        record = m.AuditLog(
            actor_id=actor_uuid,
            action=f"security.{event.operation}",
            target_type="user" if event.account_id else "security",
            target_id=event.account_id[:36] if event.account_id else None,
            details=details,
            ip_address=str(ip_address)[:45] if isinstance(ip_address, str) else None,
            user_agent=str(user_agent)[:500] if isinstance(user_agent, str) else None,
        )
        try:
            async with self._alchemy_config.get_session() as session:
                session.add(record)
                await session.commit()
        except SQLAlchemyError:
            logger.warning(
                "Failed to persist security audit event",
                operation=event.operation,
                outcome=event.outcome,
                event_id=event.event_id,
            )
            if self._strict:
                raise

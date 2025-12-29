"""Audit log model for tracking admin and security events."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID

from advanced_alchemy.base import UUIDv7AuditBase
from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.db.models._user import User


class AuditLog(UUIDv7AuditBase):
    """Audit log for tracking system events and admin actions.

    Records who did what, when, and to what entity.
    """

    __tablename__ = "audit_log"
    __table_args__ = {"comment": "Audit trail for system events and admin actions"}

    actor_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("user_account.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    """ID of the user who performed the action (null for system events)."""

    actor_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    """Email of the actor at the time of the action (preserved even if user deleted)."""

    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    """The action performed (e.g., 'user.created', 'team.deleted', 'login.failed')."""

    target_type: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    """Type of entity affected (e.g., 'user', 'team', 'role')."""

    target_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    """ID of the target entity (as string to support different ID types)."""

    target_label: Mapped[str | None] = mapped_column(String(255), nullable=True)
    """Human-readable label for the target (e.g., user email, team name)."""

    details: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    """Additional details about the action (JSON object)."""

    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    """IP address of the request (supports IPv6)."""

    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    """User agent string from the request."""

    actor: Mapped[User | None] = relationship(lazy="joined", foreign_keys=[actor_id])

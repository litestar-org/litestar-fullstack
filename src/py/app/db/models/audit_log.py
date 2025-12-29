"""Audit log model for tracking admin and security events."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID

from advanced_alchemy.base import UUIDAuditBase
from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.db.models.user import User


class AuditLog(UUIDAuditBase):
    """Audit log for tracking system events and admin actions.

    Records who did what, when, and to what entity.
    """

    __tablename__ = "audit_log"
    __table_args__ = {"comment": "Audit trail for system events and admin actions"}

    # Actor information (who performed the action)
    actor_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("user_account.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    """ID of the user who performed the action (null for system events)."""

    actor_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    """Email of the actor at the time of the action (preserved even if user deleted)."""

    # Action information
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    """The action performed (e.g., 'user.created', 'team.deleted', 'login.failed')."""

    # Target information (what the action was performed on)
    target_type: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    """Type of entity affected (e.g., 'user', 'team', 'role')."""

    target_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    """ID of the target entity (as string to support different ID types)."""

    target_label: Mapped[str | None] = mapped_column(String(255), nullable=True)
    """Human-readable label for the target (e.g., user email, team name)."""

    # Additional context
    details: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    """Additional details about the action (JSON object)."""

    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    """IP address of the request (supports IPv6)."""

    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    """User agent string from the request."""

    # ORM Relationships
    actor: Mapped[User | None] = relationship(lazy="selectin", foreign_keys=[actor_id])

    @classmethod
    def create_log(
        cls,
        action: str,
        actor_id: UUID | None = None,
        actor_email: str | None = None,
        target_type: str | None = None,
        target_id: str | None = None,
        target_label: str | None = None,
        details: dict[str, Any] | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> "AuditLog":
        """Create a new audit log entry.

        Args:
            action: The action performed
            actor_id: ID of the user performing the action
            actor_email: Email of the actor
            target_type: Type of target entity
            target_id: ID of target entity
            target_label: Human-readable label for target
            details: Additional context
            ip_address: Request IP address
            user_agent: Request user agent

        Returns:
            New AuditLog instance
        """
        return cls(
            action=action,
            actor_id=actor_id,
            actor_email=actor_email,
            target_type=target_type,
            target_id=target_id,
            target_label=target_label,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
        )

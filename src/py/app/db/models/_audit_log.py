"""Audit log model for tracking admin and security events."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID

from advanced_alchemy.base import UUIDv7AuditBase
from advanced_alchemy.types import JsonB
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.db.models._user import User


class AuditLog(UUIDv7AuditBase):
    """Audit log for tracking system events, security events, and admin actions."""

    __tablename__ = "audit_log"
    __table_args__ = {"comment": "Audit trail for system events and admin actions"}

    actor_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("user_account.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    actor_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    target_type: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    target_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    target_label: Mapped[str | None] = mapped_column(String(255), nullable=True)
    details: Mapped[dict[str, Any] | None] = mapped_column(JsonB, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)

    actor: Mapped[User | None] = relationship(lazy="joined", foreign_keys=[actor_id])

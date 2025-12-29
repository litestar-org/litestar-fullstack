"""Add audit log table.

Revision ID: 03c4d5e6f7g8
Revises: 02b3c4d5e6f7
Create Date: 2025-12-29 17:00:00.000000

"""
from __future__ import annotations

import warnings
from typing import TYPE_CHECKING

import sqlalchemy as sa
from advanced_alchemy.types import GUID, DateTimeUTC
from alembic import op
from sqlalchemy.dialects import postgresql

if TYPE_CHECKING:
    from collections.abc import Sequence

__all__ = ["downgrade", "upgrade"]

# revision identifiers, used by Alembic.
revision: str = "03c4d5e6f7g8"
down_revision: str | None = "02b3c4d5e6f7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Apply the upgrade migration."""
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        op.create_table(
            "audit_log",
            sa.Column("actor_id", GUID(length=16), nullable=True),
            sa.Column("actor_email", sa.String(length=255), nullable=True),
            sa.Column("action", sa.String(length=100), nullable=False),
            sa.Column("target_type", sa.String(length=50), nullable=True),
            sa.Column("target_id", sa.String(length=36), nullable=True),
            sa.Column("target_label", sa.String(length=255), nullable=True),
            sa.Column("details", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column("ip_address", sa.String(length=45), nullable=True),
            sa.Column("user_agent", sa.String(length=500), nullable=True),
            sa.Column("id", GUID(length=16), nullable=False),
            sa.Column("created_at", DateTimeUTC(timezone=True), nullable=False),
            sa.Column("updated_at", DateTimeUTC(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(
                ["actor_id"],
                ["user_account.id"],
                name=op.f("fk_audit_log_actor_id_user_account"),
                ondelete="SET NULL",
            ),
            sa.PrimaryKeyConstraint("id", name=op.f("pk_audit_log")),
            comment="Audit trail for system events and admin actions",
        )
        op.create_index(op.f("ix_audit_log_action"), "audit_log", ["action"], unique=False)
        op.create_index(op.f("ix_audit_log_actor_id"), "audit_log", ["actor_id"], unique=False)
        op.create_index(op.f("ix_audit_log_target_id"), "audit_log", ["target_id"], unique=False)
        op.create_index(op.f("ix_audit_log_target_type"), "audit_log", ["target_type"], unique=False)


def downgrade() -> None:
    """Reverse the upgrade migration."""
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        op.drop_index(op.f("ix_audit_log_target_type"), table_name="audit_log")
        op.drop_index(op.f("ix_audit_log_target_id"), table_name="audit_log")
        op.drop_index(op.f("ix_audit_log_actor_id"), table_name="audit_log")
        op.drop_index(op.f("ix_audit_log_action"), table_name="audit_log")
        op.drop_table("audit_log")

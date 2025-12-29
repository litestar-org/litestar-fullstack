"""Add refresh token table.

Revision ID: 01a2b3c4d5e6
Revises: bdb140899b43
Create Date: 2025-12-29 15:30:00.000000

"""
from __future__ import annotations

import warnings
from typing import TYPE_CHECKING

import sqlalchemy as sa
from advanced_alchemy.types import GUID, DateTimeUTC
from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence

__all__ = ["downgrade", "upgrade"]

# revision identifiers, used by Alembic.
revision: str = "01a2b3c4d5e6"
down_revision: str | None = "bdb140899b43"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Apply the upgrade migration."""
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        op.create_table(
            "refresh_token",
            sa.Column("user_id", GUID(length=16), nullable=False),
            sa.Column("token_hash", sa.String(length=64), nullable=False),
            sa.Column("family_id", GUID(length=16), nullable=False),
            sa.Column("expires_at", DateTimeUTC(timezone=True), nullable=False),
            sa.Column("revoked_at", DateTimeUTC(timezone=True), nullable=True),
            sa.Column("device_info", sa.String(length=255), nullable=True),
            sa.Column("id", GUID(length=16), nullable=False),
            sa.Column("created_at", DateTimeUTC(timezone=True), nullable=False),
            sa.Column("updated_at", DateTimeUTC(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(
                ["user_id"],
                ["user_account.id"],
                name=op.f("fk_refresh_token_user_id_user_account"),
                ondelete="CASCADE",
            ),
            sa.PrimaryKeyConstraint("id", name=op.f("pk_refresh_token")),
            comment="JWT refresh tokens with rotation tracking",
        )
        op.create_index(op.f("ix_refresh_token_family_id"), "refresh_token", ["family_id"], unique=False)
        op.create_index(op.f("ix_refresh_token_token_hash"), "refresh_token", ["token_hash"], unique=True)
        op.create_index(op.f("ix_refresh_token_user_id"), "refresh_token", ["user_id"], unique=False)


def downgrade() -> None:
    """Reverse the upgrade migration."""
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        op.drop_index(op.f("ix_refresh_token_user_id"), table_name="refresh_token")
        op.drop_index(op.f("ix_refresh_token_token_hash"), table_name="refresh_token")
        op.drop_index(op.f("ix_refresh_token_family_id"), table_name="refresh_token")
        op.drop_table("refresh_token")

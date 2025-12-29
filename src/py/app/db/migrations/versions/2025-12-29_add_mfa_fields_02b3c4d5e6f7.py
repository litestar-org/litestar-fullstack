"""Add MFA fields to user table.

Revision ID: 02b3c4d5e6f7
Revises: 01a2b3c4d5e6
Create Date: 2025-12-29 16:00:00.000000

"""
from __future__ import annotations

import warnings
from typing import TYPE_CHECKING

import sqlalchemy as sa
from advanced_alchemy.types import DateTimeUTC
from alembic import op
from sqlalchemy.dialects import postgresql

if TYPE_CHECKING:
    from collections.abc import Sequence

__all__ = ["downgrade", "upgrade"]

# revision identifiers, used by Alembic.
revision: str = "02b3c4d5e6f7"
down_revision: str | None = "01a2b3c4d5e6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Apply the upgrade migration."""
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        op.add_column(
            "user_account",
            sa.Column("totp_secret", sa.String(length=255), nullable=True),
        )
        op.add_column(
            "user_account",
            sa.Column("is_two_factor_enabled", sa.Boolean(), nullable=False, server_default="false"),
        )
        op.add_column(
            "user_account",
            sa.Column("two_factor_confirmed_at", DateTimeUTC(timezone=True), nullable=True),
        )
        op.add_column(
            "user_account",
            sa.Column("backup_codes", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        )


def downgrade() -> None:
    """Reverse the upgrade migration."""
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        op.drop_column("user_account", "backup_codes")
        op.drop_column("user_account", "two_factor_confirmed_at")
        op.drop_column("user_account", "is_two_factor_enabled")
        op.drop_column("user_account", "totp_secret")

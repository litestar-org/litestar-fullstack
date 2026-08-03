"""replace avatar_url with avatar file object

Revision ID: 75cc19aa927c
Revises: dc54b25d8b6c
Create Date: 2026-04-08 13:45:00.000000

"""
import warnings

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '75cc19aa927c'
down_revision = 'dc54b25d8b6c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=UserWarning)
        with op.get_context().autocommit_block():
            schema_upgrades()
            data_upgrades()

def downgrade() -> None:
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=UserWarning)
        with op.get_context().autocommit_block():
            data_downgrades()
            schema_downgrades()

def schema_upgrades() -> None:
    with op.batch_alter_table('user_account', schema=None) as batch_op:
        batch_op.drop_column('avatar_url')
        batch_op.add_column(sa.Column('avatar', postgresql.JSONB(), nullable=True))

def schema_downgrades() -> None:
    with op.batch_alter_table('user_account', schema=None) as batch_op:
        batch_op.drop_column('avatar')
        batch_op.add_column(sa.Column('avatar_url', sa.String(length=500), nullable=True))

def data_upgrades() -> None:
    """No data migration needed — column change only."""

def data_downgrades() -> None:
    """No data migration needed — column change only."""

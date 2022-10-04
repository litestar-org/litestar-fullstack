# type: ignore
"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from app.core.db.db_types import GUID, EmailString, JsonObject, PydanticType, TimestampAwareDateTime
${imports if imports else ""}

sa.GUID = GUID
sa.EmailString = EmailString
sa.JsonObject = JsonObject
sa.PydanticType = PydanticType
sa.TimestampAwareDateTime = TimestampAwareDateTime

# revision identifiers, used by Alembic.
revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}


def upgrade():
    ${upgrades if upgrades else "pass"}


def downgrade():
    ${downgrades if downgrades else "pass"}

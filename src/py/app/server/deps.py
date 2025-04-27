"""Collection routes."""

from __future__ import annotations

from sqlalchemy.orm import joinedload, load_only, selectinload

from app.db import models as m
from app.lib.deps import create_service_provider
from app.services import UserService

provide_users_service = create_service_provider(
    UserService,
    load=[
        joinedload(m.User.roles).options(joinedload(m.UserRole.role, innerjoin=True)),
        joinedload(m.User.oauth_accounts),
        selectinload(m.User.teams).options(
            joinedload(m.TeamMember.team, innerjoin=True).options(load_only(m.Team.name)),
        ),
    ],
    uniquify=True,
    error_messages={"duplicate_key": "This user already exists.", "integrity": "User operation failed."},
)

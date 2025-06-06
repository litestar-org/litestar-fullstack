"""Collection routes."""

from __future__ import annotations

from sqlalchemy.orm import joinedload, load_only, selectinload

from app.db import models as m
from app.lib.deps import create_service_provider
from app.services import UserService
from app.services._email_verification import EmailVerificationTokenService
from app.services._password_reset import PasswordResetService

provide_users_service = create_service_provider(
    UserService,
    load=[
        selectinload(m.User.roles).options(joinedload(m.UserRole.role, innerjoin=True)),
        selectinload(m.User.oauth_accounts),
        selectinload(m.User.teams).options(
            joinedload(m.TeamMember.team, innerjoin=True).options(load_only(m.Team.name)),
        ),
    ],
    uniquify=True,
    error_messages={"duplicate_key": "This user already exists.", "integrity": "User operation failed."},
)

provide_email_verification_service = create_service_provider(
    EmailVerificationTokenService,
    load=[
        selectinload(m.EmailVerificationToken.user),
    ],
    error_messages={
        "duplicate_key": "Verification token already exists.",
        "integrity": "Email verification operation failed.",
    },
)

provide_password_reset_service = create_service_provider(
    PasswordResetService,
    load=[
        selectinload(m.PasswordResetToken.user),
    ],
    error_messages={
        "duplicate_key": "Reset token already exists.",
        "integrity": "Password reset operation failed.",
    },
)

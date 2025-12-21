"""Account domain dependencies."""

from __future__ import annotations

from sqlalchemy.orm import joinedload, load_only, selectinload

from app.db import models as m
from app.domain.accounts.services import (
    EmailVerificationTokenService,
    PasswordResetService,
    RoleService,
    UserOAuthAccountService,
    UserRoleService,
    UserService,
)
from app.lib.deps import create_service_provider

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

provide_roles_service = create_service_provider(
    RoleService,
    load=[selectinload(m.Role.users)],
    error_messages={
        "duplicate_key": "This role already exists.",
        "integrity": "Role operation failed.",
    },
)

provide_user_roles_service = create_service_provider(
    UserRoleService,
    load=[
        selectinload(m.UserRole.user),
        selectinload(m.UserRole.role),
    ],
    error_messages={
        "duplicate_key": "User already has this role.",
        "integrity": "User role operation failed.",
    },
)

provide_user_oauth_service = create_service_provider(
    UserOAuthAccountService,
    load=[selectinload(m.UserOAuthAccount.user)],
    error_messages={
        "duplicate_key": "OAuth account already linked.",
        "integrity": "OAuth account operation failed.",
    },
)

__all__ = (
    "provide_email_verification_service",
    "provide_password_reset_service",
    "provide_roles_service",
    "provide_user_oauth_service",
    "provide_user_roles_service",
    "provide_users_service",
)

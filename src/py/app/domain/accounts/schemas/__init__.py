"""Account domain schemas."""

from __future__ import annotations

from app.domain.accounts.schemas._api_key import APIKeyCreate, APIKeyIssued, APIKeyItem
from app.domain.accounts.schemas._role import Role, RoleCreate, RoleUpdate, UserRoleAdd, UserRoleRevoke
from app.domain.accounts.schemas._user import (
    OauthAccount,
    PasswordConfirmation,
    PasswordUpdate,
    ProfileUpdate,
    User,
    UserCreate,
    UserRole,
    UserTeam,
    UserUpdate,
)
from app.lib.schema import Message

__all__ = (
    "APIKeyCreate",
    "APIKeyIssued",
    "APIKeyItem",
    "Message",
    "OauthAccount",
    "PasswordConfirmation",
    "PasswordUpdate",
    "ProfileUpdate",
    "Role",
    "RoleCreate",
    "RoleUpdate",
    "User",
    "UserCreate",
    "UserRole",
    "UserRoleAdd",
    "UserRoleRevoke",
    "UserTeam",
    "UserUpdate",
)

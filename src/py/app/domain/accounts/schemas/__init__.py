"""Account domain schemas."""

from __future__ import annotations

from app.domain.accounts.schemas._api_keys import APIKeyCreate, APIKeyIssued, APIKeyItem
from app.domain.accounts.schemas._roles import Role, RoleCreate, RoleUpdate, UserRoleAdd, UserRoleRevoke
from app.domain.accounts.schemas._user import (
    OauthAccount,
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

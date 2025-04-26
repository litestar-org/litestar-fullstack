from __future__ import annotations

from enum import Enum


class TeamRoles(str, Enum):
    """Valid Values for Team Roles."""

    ADMIN = "ADMIN"
    MEMBER = "MEMBER"

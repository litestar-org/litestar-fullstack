from uuid import UUID

import msgspec

from app.db import models as m
from app.schemas.base import CamelizedBaseStruct


class TeamTag(CamelizedBaseStruct):
    id: UUID
    slug: str
    name: str


class TeamMember(CamelizedBaseStruct):
    id: UUID
    user_id: UUID
    email: str
    name: str | None = None
    role: m.TeamRoles | None = m.TeamRoles.MEMBER
    is_owner: bool | None = False


class Team(CamelizedBaseStruct):
    id: UUID
    name: str
    description: str | None = None
    members: list[TeamMember] = []
    tags: list[TeamTag] = []


class TeamCreate(CamelizedBaseStruct):
    name: str
    description: str | None = None
    tags: list[str] = []


class TeamUpdate(CamelizedBaseStruct, omit_defaults=True):
    name: str | msgspec.UnsetType | None = msgspec.UNSET
    description: str | msgspec.UnsetType | None = msgspec.UNSET
    tags: list[str] | msgspec.UnsetType | None = msgspec.UNSET


class TeamMemberModify(CamelizedBaseStruct):
    """Team Member Modify."""

    user_name: str

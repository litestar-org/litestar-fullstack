"""Team schemas."""

from uuid import UUID

import msgspec

from app.domain.teams.schemas._member import TeamMember
from app.lib.schema import CamelizedBaseStruct


class TeamTag(CamelizedBaseStruct):
    id: UUID
    slug: str
    name: str


class Team(CamelizedBaseStruct):
    id: UUID
    name: str
    slug: str
    description: str | None = None
    is_active: bool = True
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

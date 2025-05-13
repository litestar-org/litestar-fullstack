from datetime import datetime
from uuid import UUID

import msgspec
from litestar.datastructures import UploadFile

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


class TeamFileUpload(CamelizedBaseStruct):
    """Attributes required to post to the collection upload endpoint."""

    files: list[UploadFile]

    def __post_init__(self) -> None:
        if isinstance(self.files, UploadFile):
            self.files = [self.files]
        if not isinstance(self.files, list):  # pyright: ignore
            msg = "Unable to parse attached files"  # type: ignore[unreachable]
            raise TypeError(msg)


class TeamFile(CamelizedBaseStruct):
    id: UUID
    name: str
    url: str
    created_at: datetime
    updated_at: datetime


class TeamInvitationCreate(CamelizedBaseStruct):
    email: str
    role: m.TeamRoles


class TeamInvitation(CamelizedBaseStruct):
    id: UUID
    email: str
    role: m.TeamRoles
    created_at: datetime
    updated_at: datetime

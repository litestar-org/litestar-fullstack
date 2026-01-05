from __future__ import annotations

from advanced_alchemy.extensions.litestar import repository, service

from app.db import models as m


class TeamInvitationService(service.SQLAlchemyAsyncRepositoryService[m.TeamInvitation]):
    """Team Invitation Service."""

    class Repo(repository.SQLAlchemyAsyncRepository[m.TeamInvitation]):
        """Team Invitation Repository."""

        model_type = m.TeamInvitation

    repository_type = Repo

    async def to_model_on_create(
        self, data: service.ModelDictT[m.TeamInvitation]
    ) -> service.ModelDictT[m.TeamInvitation]:
        data = service.schema_dump(data)
        return await self._populate_inviter(data)

    async def to_model_on_update(
        self, data: service.ModelDictT[m.TeamInvitation]
    ) -> service.ModelDictT[m.TeamInvitation]:
        data = service.schema_dump(data)
        return await self._populate_inviter(data)

    async def to_model_on_upsert(
        self, data: service.ModelDictT[m.TeamInvitation]
    ) -> service.ModelDictT[m.TeamInvitation]:
        data = service.schema_dump(data)
        return await self._populate_inviter(data)

    async def _populate_inviter(
        self, data: service.ModelDictT[m.TeamInvitation]
    ) -> service.ModelDictT[m.TeamInvitation]:
        if not service.is_dict(data):
            return data
        inviter = data.pop("invited_by", None)
        if inviter is None:
            return data
        if service.is_dict_without_field(data, "invited_by_id"):
            data["invited_by_id"] = inviter.id
        if service.is_dict_without_field(data, "invited_by_email"):
            data["invited_by_email"] = inviter.email
        return data

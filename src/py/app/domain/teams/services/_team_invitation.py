"""Team invitation database service using AA 1.13 inferred default repository."""

from __future__ import annotations

from advanced_alchemy.extensions.litestar import service

from app.db import models as m


class TeamInvitationService(service.SQLAlchemyAsyncRepositoryService[m.TeamInvitation]):
    """Team invitation CRUD service."""

    async def to_model_on_create(
        self, data: service.ModelDictT[m.TeamInvitation]
    ) -> service.ModelDictT[m.TeamInvitation]:
        """Resolve inviter metadata before creating an invitation.

        Returns:
            Normalized invitation payload with inviter fields populated.
        """
        return await self._populate_inviter(service.schema_dump(data))

    async def to_model_on_update(
        self, data: service.ModelDictT[m.TeamInvitation]
    ) -> service.ModelDictT[m.TeamInvitation]:
        """Resolve inviter metadata before updating an invitation.

        Returns:
            Normalized invitation payload with inviter fields populated.
        """
        return await self._populate_inviter(service.schema_dump(data))

    async def to_model_on_upsert(
        self, data: service.ModelDictT[m.TeamInvitation]
    ) -> service.ModelDictT[m.TeamInvitation]:
        """Resolve inviter metadata before upserting an invitation.

        Returns:
            Normalized invitation payload with inviter fields populated.
        """
        return await self._populate_inviter(service.schema_dump(data))

    async def _populate_inviter(
        self, data: service.ModelDictT[m.TeamInvitation]
    ) -> service.ModelDictT[m.TeamInvitation]:
        if not service.is_dict(data):
            return data
        if (inviter := data.pop("invited_by", None)) is None:
            return data
        if service.is_dict_without_field(data, "invited_by_id"):
            data["invited_by_id"] = inviter.id
        if service.is_dict_without_field(data, "invited_by_email"):
            data["invited_by_email"] = inviter.email
        return data

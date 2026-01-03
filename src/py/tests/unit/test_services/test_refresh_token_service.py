from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from litestar.exceptions import NotAuthorizedException

from app.db import models as m
from app.domain.accounts.services import RefreshTokenService
from tests.factories import UserFactory

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

pytestmark = [pytest.mark.unit, pytest.mark.auth, pytest.mark.services]


@pytest.mark.asyncio
async def test_rotate_refresh_token_revokes_old_token(
    session: AsyncSession,
    sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    user = UserFactory.build()
    session.add(user)
    await session.commit()

    async with RefreshTokenService.new(sessionmaker()) as service:
        raw_token, old_token = await service.create_refresh_token(user_id=user.id)
        new_raw_token, new_token = await service.rotate_refresh_token(raw_token)

        refreshed_old = await service.get(old_token.id)

        assert new_raw_token != raw_token
        assert new_token.family_id == old_token.family_id
        assert refreshed_old.revoked_at is not None


@pytest.mark.asyncio
async def test_reuse_detection_revokes_family(
    session: AsyncSession,
    sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    user = UserFactory.build()
    session.add(user)
    await session.commit()

    async with RefreshTokenService.new(sessionmaker()) as service:
        raw_token, old_token = await service.create_refresh_token(user_id=user.id)
        _, rotated = await service.rotate_refresh_token(raw_token)

        with pytest.raises(NotAuthorizedException):
            await service.rotate_refresh_token(raw_token)

        revoked_tokens = await service.list(m.RefreshToken.family_id == old_token.family_id)
        assert all(token.revoked_at is not None for token in revoked_tokens)
        refreshed_rotated = await service.get(rotated.id)
        assert refreshed_rotated.revoked_at is not None

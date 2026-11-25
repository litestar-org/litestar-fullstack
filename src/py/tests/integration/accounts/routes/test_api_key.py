"""PostgreSQL integration tests for personal API key issuance, Bearer authentication, rotation, and revocation."""

from __future__ import annotations

import asyncio
from secrets import token_bytes
from typing import TYPE_CHECKING

import pytest
from litestar_security.providers.api_key import IssuedAPIKey
from sqlalchemy import select

from app import config
from app.db import models as m
from app.domain.accounts.security import SQLAlchemyAPIKeyStore, build_api_key_service
from tests.integration.conftest import login_session_client, reset_client_session

if TYPE_CHECKING:
    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

pytestmark = [pytest.mark.anyio, pytest.mark.integration, pytest.mark.auth, pytest.mark.security]


async def test_api_key_lifecycle_hash_storage_rotation_and_revocation(
    client: AsyncClient,
    session: AsyncSession,
    test_user: m.User,
) -> None:
    """API keys reveal plaintext once, store only hashes, authenticate Bearer calls, and invalidate on rotate/revoke."""
    csrf = await login_session_client(client, test_user.email, "TestPassword123!")
    create_res = await client.post(
        "/api/me/api-keys",
        json={"name": "CI Key", "scopes": ["read", "mcp"], "expiresInDays": 30},
        headers=csrf,
    )
    assert create_res.status_code == 201, create_res.text
    issued = create_res.json()
    key_id = issued["id"]
    raw_secret = issued["secret"]
    assert raw_secret

    db_key = await session.scalar(select(m.APIKey).where(m.APIKey.key_id == key_id))
    assert db_key is not None
    assert db_key.key_hash != raw_secret

    list_res = await client.get("/api/me/api-keys")
    assert list_res.status_code == 200
    items = list_res.json()
    assert len(items) == 1
    assert "secret" not in items[0]
    assert items[0]["prefix"] == issued["prefix"]

    reset_client_session(client)
    ok_res = await client.get("/api/me", headers={"Authorization": f"Bearer {raw_secret}"})
    assert ok_res.status_code == 200
    assert ok_res.json()["email"] == test_user.email

    csrf = await login_session_client(client, test_user.email, "TestPassword123!")
    rotate_res = await client.post(f"/api/me/api-keys/{key_id}/rotate", headers=csrf)
    assert rotate_res.status_code == 201, rotate_res.text
    rotated = rotate_res.json()
    new_key_id = rotated["id"]
    new_secret = rotated["secret"]
    assert new_secret != raw_secret

    reset_client_session(client)
    overlap_old_res = await client.get("/api/me", headers={"Authorization": f"Bearer {raw_secret}"})
    assert overlap_old_res.status_code == 200
    new_res = await client.get("/api/me", headers={"Authorization": f"Bearer {new_secret}"})
    assert new_res.status_code == 200

    csrf = await login_session_client(client, test_user.email, "TestPassword123!")
    assert (await client.delete(f"/api/me/api-keys/{key_id}", headers=csrf)).status_code == 204
    assert (await client.delete(f"/api/me/api-keys/{new_key_id}", headers=csrf)).status_code == 204

    reset_client_session(client)
    assert (await client.get("/api/me", headers={"Authorization": f"Bearer {raw_secret}"})).status_code == 401
    assert (await client.get("/api/me", headers={"Authorization": f"Bearer {new_secret}"})).status_code == 401


async def test_concurrent_rotations_of_one_key_have_a_single_winner(
    sessionmaker: async_sessionmaker[AsyncSession],
    test_user: m.User,
) -> None:
    """Two rotations that both read the same live key yield exactly one replacement and one conflict."""
    api_key_service = build_api_key_service(SQLAlchemyAPIKeyStore(config.alchemy), token_bytes(32))
    subject_id = str(test_user.id)
    issued = await api_key_service.issue(subject_id=subject_id)

    async with sessionmaker() as db_session:
        await db_session.execute(select(m.APIKey.id).where(m.APIKey.key_id == issued.key_id).with_for_update())

        async def unlock_key_after_both_rotations_read_it() -> None:
            await asyncio.sleep(0.5)
            await db_session.commit()

        first, second, _ = await asyncio.gather(
            api_key_service.rotate(current_key_id=issued.key_id, subject_id=subject_id),
            api_key_service.rotate(current_key_id=issued.key_id, subject_id=subject_id),
            unlock_key_after_both_rotations_read_it(),
            return_exceptions=True,
        )
        successors = await db_session.scalars(select(m.APIKey).where(m.APIKey.rotated_from_id.is_not(None)))
        successor_key_ids = [successor.key_id for successor in successors]

    replacements = [outcome for outcome in (first, second) if isinstance(outcome, IssuedAPIKey)]
    conflicts = [outcome for outcome in (first, second) if isinstance(outcome, ValueError)]
    assert len(replacements) == 1
    assert len(conflicts) == 1
    assert successor_key_ids == [replacements[0].key_id]

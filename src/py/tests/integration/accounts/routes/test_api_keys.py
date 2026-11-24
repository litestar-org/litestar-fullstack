"""PostgreSQL integration tests for personal API key issuance, Bearer authentication, rotation, and revocation."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from sqlalchemy import select

from app.db import models as m
from tests.integration.conftest import login_session_client, reset_client_session

if TYPE_CHECKING:
    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession

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

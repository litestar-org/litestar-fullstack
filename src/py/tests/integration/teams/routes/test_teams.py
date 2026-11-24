"""Integration tests for team CRUD routes and tenant role guard matrix."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

import pytest
from litestar_security.accounts import Argon2PasswordHasher
from sqlalchemy import select

from app.db import models as m
from tests.integration.conftest import fetch_csrf_headers, login_session_client, reset_client_session

if TYPE_CHECKING:
    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = [pytest.mark.anyio, pytest.mark.integration, pytest.mark.teams, pytest.mark.endpoints]

_HASHER = Argon2PasswordHasher()


async def _create_user(session: AsyncSession, email: str, *, is_superuser: bool = False) -> m.User:
    """Persist an active verified user with a known Argon2 password."""
    user = m.User(
        email=email,
        name=email.split("@", maxsplit=1)[0],
        hashed_password=await _HASHER.hash("TestPassword123!"),
        is_active=True,
        is_verified=True,
        is_superuser=is_superuser,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def test_team_crud_as_owner_with_db_verification(
    authenticated_client: AsyncClient,
    test_user: m.User,
    session: AsyncSession,
) -> None:
    """Creating, reading, updating, and deleting a team persists owner membership and tags."""
    create_resp = await authenticated_client.post(
        "/api/teams",
        json={"name": "Engineering Core", "description": "Platform team", "tags": ["platform", "api"]},
    )
    assert create_resp.status_code == 201, create_resp.text
    created = create_resp.json()
    team_id = created["id"]
    assert created["name"] == "Engineering Core"
    assert created["isActive"] is True
    assert len(created["members"]) == 1
    assert created["members"][0]["email"] == test_user.email
    assert created["members"][0]["isOwner"] is True
    assert created["members"][0]["role"] == m.TeamRoles.ADMIN.value

    list_resp = await authenticated_client.get("/api/teams")
    assert list_resp.status_code == 200
    assert team_id in [item["id"] for item in list_resp.json()["items"]]

    detail_resp = await authenticated_client.get(f"/api/teams/{team_id}")
    assert detail_resp.status_code == 200
    assert detail_resp.json()["description"] == "Platform team"

    update_resp = await authenticated_client.patch(
        f"/api/teams/{team_id}",
        json={"name": "Engineering Platform", "description": "Updated platform team"},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["name"] == "Engineering Platform"

    delete_resp = await authenticated_client.delete(f"/api/teams/{team_id}")
    assert delete_resp.status_code == 204

    deleted = await session.scalar(select(m.Team).where(m.Team.id == created["id"]))
    assert deleted is None


async def test_team_endpoints_reject_unauthenticated_and_invalid_payloads(
    client: AsyncClient,
    test_user: m.User,
    test_team: m.Team,
) -> None:
    """Unauthenticated callers get 401 and invalid create payloads return 400."""
    unauth_csrf = await fetch_csrf_headers(client)
    assert (await client.get("/api/teams")).status_code == 401
    assert (await client.post("/api/teams", json={"name": "No Auth"}, headers=unauth_csrf)).status_code == 401
    assert (await client.get(f"/api/teams/{test_team.id}")).status_code == 401

    auth_csrf = await login_session_client(client, test_user.email, "TestPassword123!")
    invalid_resp = await client.post("/api/teams", json={"description": "Missing name"}, headers=auth_csrf)
    assert invalid_resp.status_code == 400

    missing_team_resp = await client.get(f"/api/teams/{uuid4()}")
    assert missing_team_resp.status_code == 403


async def test_team_tenant_guard_matrix(
    client: AsyncClient,
    session: AsyncSession,
    test_team: m.Team,
    test_team_member: m.User,
) -> None:
    """Verify tenant isolation across non-member, team MEMBER, and superuser callers."""
    outsider = await _create_user(session, "outsider@example.com")
    superuser = await _create_user(session, "teamadmin@example.com", is_superuser=True)

    outsider_csrf = await login_session_client(client, outsider.email, "TestPassword123!")
    listed = await client.get("/api/teams")
    assert listed.status_code == 200
    assert str(test_team.id) not in [item["id"] for item in listed.json()["items"]]
    assert (await client.get(f"/api/teams/{test_team.id}")).status_code == 403
    assert (
        await client.patch(
            f"/api/teams/{test_team.id}",
            json={"name": "Hijack"},
            headers=outsider_csrf,
        )
    ).status_code == 403
    assert (await client.delete(f"/api/teams/{test_team.id}", headers=outsider_csrf)).status_code == 403

    reset_client_session(client)
    member_csrf = await login_session_client(client, test_team_member.email, "TestPassword123!")
    assert (await client.get(f"/api/teams/{test_team.id}")).status_code == 200
    assert (
        await client.patch(
            f"/api/teams/{test_team.id}",
            json={"name": "Member Cannot Update"},
            headers=member_csrf,
        )
    ).status_code == 403
    assert (await client.delete(f"/api/teams/{test_team.id}", headers=member_csrf)).status_code == 403

    reset_client_session(client)
    super_csrf = await login_session_client(client, superuser.email, "TestPassword123!")
    assert (await client.get(f"/api/teams/{test_team.id}")).status_code == 200
    super_patch = await client.patch(
        f"/api/teams/{test_team.id}",
        json={"name": "Superuser Updated"},
        headers=super_csrf,
    )
    assert super_patch.status_code == 200
    assert super_patch.json()["name"] == "Superuser Updated"

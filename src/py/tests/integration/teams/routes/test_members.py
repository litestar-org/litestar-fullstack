"""Integration tests for team member endpoints and tenant admin guard enforcement."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

import pytest
from litestar_security.accounts import Argon2PasswordHasher
from sqlalchemy import select

from app.db import models as m
from tests.factories import grant_application_access
from tests.integration.conftest import fetch_csrf_headers, login_session_client, reset_client_session

if TYPE_CHECKING:
    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = [pytest.mark.anyio, pytest.mark.integration, pytest.mark.teams, pytest.mark.endpoints]

_HASHER = Argon2PasswordHasher()


async def _create_user(session: AsyncSession, email: str) -> m.User:
    """Create an active verified user for membership operations."""
    user = m.User(
        email=email,
        name=email.split("@", maxsplit=1)[0],
        hashed_password=await _HASHER.hash("TestPassword123!"),
        is_active=True,
        is_verified=True,
        is_superuser=False,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    await grant_application_access(session, user)
    return user


async def test_add_update_and_remove_team_member_lifecycle(
    authenticated_client: AsyncClient,
    test_team: m.Team,
    test_user: m.User,
    session: AsyncSession,
) -> None:
    """Team admins can add members, promote/demote roles, and remove non-owner members."""
    candidate = await _create_user(session, f"candidate-{uuid4().hex[:8]}@example.com")

    add_resp = await authenticated_client.post(
        f"/api/teams/{test_team.id}/members",
        json={"userName": candidate.email},
    )
    assert add_resp.status_code == 201, add_resp.text
    assert candidate.email in [member["email"] for member in add_resp.json()["members"]]

    duplicate_resp = await authenticated_client.post(
        f"/api/teams/{test_team.id}/members",
        json={"userName": candidate.email},
    )
    assert duplicate_resp.status_code == 409

    promote_resp = await authenticated_client.patch(
        f"/api/teams/{test_team.id}/members/{candidate.id}",
        json={"role": m.TeamRoles.ADMIN.value},
    )
    assert promote_resp.status_code == 200
    assert promote_resp.json()["role"] == m.TeamRoles.ADMIN.value

    demote_resp = await authenticated_client.patch(
        f"/api/teams/{test_team.id}/members/{candidate.id}",
        json={"role": m.TeamRoles.MEMBER.value},
    )
    assert demote_resp.status_code == 200
    assert demote_resp.json()["role"] == m.TeamRoles.MEMBER.value

    invalid_role_resp = await authenticated_client.patch(
        f"/api/teams/{test_team.id}/members/{candidate.id}",
        json={"role": "INVALID_ROLE"},
    )
    assert invalid_role_resp.status_code == 400

    remove_owner_resp = await authenticated_client.request(
        "DELETE",
        f"/api/teams/{test_team.id}/members",
        json={"userName": test_user.email},
    )
    assert remove_owner_resp.status_code == 400

    remove_resp = await authenticated_client.request(
        "DELETE",
        f"/api/teams/{test_team.id}/members",
        json={"userName": candidate.email},
    )
    assert remove_resp.status_code == 202
    assert candidate.email not in [member["email"] for member in remove_resp.json()["members"]]

    remaining = await session.scalar(
        select(m.TeamMember).where(m.TeamMember.team_id == test_team.id, m.TeamMember.user_id == candidate.id)
    )
    assert remaining is None


async def test_member_error_conditions(
    authenticated_client: AsyncClient,
    test_team: m.Team,
    session: AsyncSession,
) -> None:
    """Missing users return 404 and non-members return 409 on removal or role update."""
    outsider = await _create_user(session, f"notmember-{uuid4().hex[:8]}@example.com")

    assert (
        await authenticated_client.post(
            f"/api/teams/{test_team.id}/members",
            json={"userName": "missing-user@example.com"},
        )
    ).status_code == 404

    assert (
        await authenticated_client.request(
            "DELETE",
            f"/api/teams/{test_team.id}/members",
            json={"userName": "missing-user@example.com"},
        )
    ).status_code == 404

    assert (
        await authenticated_client.request(
            "DELETE",
            f"/api/teams/{test_team.id}/members",
            json={"userName": outsider.email},
        )
    ).status_code == 409

    assert (
        await authenticated_client.patch(
            f"/api/teams/{test_team.id}/members/{outsider.id}",
            json={"role": m.TeamRoles.ADMIN.value},
        )
    ).status_code == 409


async def test_member_mutations_require_team_admin_role(
    client: AsyncClient,
    session: AsyncSession,
    test_team: m.Team,
    test_team_member: m.User,
) -> None:
    """Unauthenticated callers get 401 and regular team MEMBERs or outsiders get 403."""
    target = await _create_user(session, f"target-{uuid4().hex[:8]}@example.com")
    outsider = await _create_user(session, f"outsider-mem-{uuid4().hex[:8]}@example.com")

    unauth_csrf = await fetch_csrf_headers(client)
    assert (
        await client.post(
            f"/api/teams/{test_team.id}/members",
            json={"userName": target.email},
            headers=unauth_csrf,
        )
    ).status_code == 401
    assert (
        await client.patch(
            f"/api/teams/{test_team.id}/members/{test_team_member.id}",
            json={"role": m.TeamRoles.ADMIN.value},
            headers=unauth_csrf,
        )
    ).status_code == 401

    member_csrf = await login_session_client(client, test_team_member.email, "TestPassword123!")
    assert (
        await client.post(
            f"/api/teams/{test_team.id}/members",
            json={"userName": target.email},
            headers=member_csrf,
        )
    ).status_code == 403
    assert (
        await client.patch(
            f"/api/teams/{test_team.id}/members/{test_team_member.id}",
            json={"role": m.TeamRoles.ADMIN.value},
            headers=member_csrf,
        )
    ).status_code == 403

    reset_client_session(client)
    outsider_csrf = await login_session_client(client, outsider.email, "TestPassword123!")
    assert (
        await client.post(
            f"/api/teams/{test_team.id}/members",
            json={"userName": target.email},
            headers=outsider_csrf,
        )
    ).status_code == 403

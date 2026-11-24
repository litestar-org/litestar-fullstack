"""Integration tests for team invitation routes, tenant guards, and queued email dispatch."""

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


async def _create_user(session: AsyncSession, email: str) -> m.User:
    """Create an active verified user for invitation workflows."""
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
    return user


async def test_create_list_and_delete_team_invitation(
    authenticated_client: AsyncClient,
    test_team: m.Team,
    test_user: m.User,
    session: AsyncSession,
) -> None:
    """Team admins can create, list, and revoke invitations and enqueue the invitation email task."""
    invitee_email = f"invitee-{uuid4().hex[:8]}@example.com"

    create_resp = await authenticated_client.post(
        f"/api/teams/{test_team.id}/invitations",
        json={"email": invitee_email, "role": m.TeamRoles.MEMBER.value},
    )
    assert create_resp.status_code == 201, create_resp.text
    invitation = create_resp.json()
    assert invitation["email"] == invitee_email
    assert invitation["isAccepted"] is False

    queued_task = await session.scalar(
        select(m.QueueTask)
        .where(m.QueueTask.task_name == "email.send_team_invitation")
        .order_by(m.QueueTask.created_at.desc())
    )
    assert queued_task is not None

    existing_member_resp = await authenticated_client.post(
        f"/api/teams/{test_team.id}/invitations",
        json={"email": test_user.email, "role": m.TeamRoles.MEMBER.value},
    )
    assert existing_member_resp.status_code == 400

    list_resp = await authenticated_client.get(f"/api/teams/{test_team.id}/invitations")
    assert list_resp.status_code == 200
    assert invitee_email in [item["email"] for item in list_resp.json()["items"]]

    delete_resp = await authenticated_client.delete(f"/api/teams/{test_team.id}/invitations/{invitation['id']}")
    assert delete_resp.status_code == 204

    after_list = await authenticated_client.get(f"/api/teams/{test_team.id}/invitations")
    assert invitee_email not in [item["email"] for item in after_list.json()["items"]]


async def test_accept_and_reject_team_invitations(
    client: AsyncClient,
    session: AsyncSession,
    test_team: m.Team,
    test_team_invitation: m.TeamInvitation,
) -> None:
    """Only the addressed user can accept or reject an invitation; replay and wrong-user calls fail."""
    invited_user = await _create_user(session, test_team_invitation.email)
    other_user = await _create_user(session, f"wrong-invitee-{uuid4().hex[:8]}@example.com")

    wrong_csrf = await login_session_client(client, other_user.email, "TestPassword123!")
    assert (
        await client.post(
            f"/api/teams/{test_team.id}/invitations/{test_team_invitation.id}/accept",
            headers=wrong_csrf,
        )
    ).status_code == 403
    assert (
        await client.post(
            f"/api/teams/{test_team.id}/invitations/{test_team_invitation.id}/reject",
            headers=wrong_csrf,
        )
    ).status_code == 403

    reset_client_session(client)
    invitee_csrf = await login_session_client(client, invited_user.email, "TestPassword123!")
    accept_resp = await client.post(
        f"/api/teams/{test_team.id}/invitations/{test_team_invitation.id}/accept",
        headers=invitee_csrf,
    )
    assert accept_resp.status_code == 201
    assert "accepted" in accept_resp.json()["message"].lower()

    replay_resp = await client.post(
        f"/api/teams/{test_team.id}/invitations/{test_team_invitation.id}/accept",
        headers=invitee_csrf,
    )
    assert replay_resp.status_code == 400

    second_invite = m.TeamInvitation(
        team_id=test_team.id,
        email=other_user.email,
        role=m.TeamRoles.MEMBER,
        is_accepted=False,
        invited_by_id=test_team_invitation.invited_by_id,
        invited_by_email=test_team_invitation.invited_by_email,
    )
    session.add(second_invite)
    await session.commit()
    await session.refresh(second_invite)

    reset_client_session(client)
    reject_csrf = await login_session_client(client, other_user.email, "TestPassword123!")
    reject_resp = await client.post(
        f"/api/teams/{test_team.id}/invitations/{second_invite.id}/reject",
        headers=reject_csrf,
    )
    assert reject_resp.status_code == 201
    assert "rejected" in reject_resp.json()["message"].lower()


async def test_invitation_tenant_guard_isolation(
    client: AsyncClient,
    session: AsyncSession,
    test_team: m.Team,
    test_team_member: m.User,
    test_team_invitation: m.TeamInvitation,
) -> None:
    """Unauthenticated callers get 401; MEMBER can list but not create/delete; outsiders get 403."""
    outsider = await _create_user(session, f"inv-outsider-{uuid4().hex[:8]}@example.com")
    unauth_csrf = await fetch_csrf_headers(client)

    assert (await client.get(f"/api/teams/{test_team.id}/invitations")).status_code == 401
    assert (
        await client.post(
            f"/api/teams/{test_team.id}/invitations",
            json={"email": "anon@example.com", "role": "MEMBER"},
            headers=unauth_csrf,
        )
    ).status_code == 401

    member_csrf = await login_session_client(client, test_team_member.email, "TestPassword123!")
    assert (await client.get(f"/api/teams/{test_team.id}/invitations")).status_code == 200
    assert (
        await client.post(
            f"/api/teams/{test_team.id}/invitations",
            json={"email": "blocked@example.com", "role": "MEMBER"},
            headers=member_csrf,
        )
    ).status_code == 403
    assert (
        await client.delete(
            f"/api/teams/{test_team.id}/invitations/{test_team_invitation.id}",
            headers=member_csrf,
        )
    ).status_code == 403

    reset_client_session(client)
    outsider_csrf = await login_session_client(client, outsider.email, "TestPassword123!")
    assert (await client.get(f"/api/teams/{test_team.id}/invitations")).status_code == 403
    assert (
        await client.post(
            f"/api/teams/{test_team.id}/invitations",
            json={"email": "outsider-blocked@example.com", "role": "MEMBER"},
            headers=outsider_csrf,
        )
    ).status_code == 403

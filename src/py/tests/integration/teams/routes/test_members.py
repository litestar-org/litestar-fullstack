"""Integration tests for team member endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

import pytest

from app.db import models as m
from app.lib.crypt import get_password_hash
from tests.factories import TeamFactory, TeamMemberFactory, UserFactory

if TYPE_CHECKING:
    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = [pytest.mark.integration, pytest.mark.endpoints, pytest.mark.auth]


async def _login_user(client: AsyncClient, user: m.User) -> str:
    """Helper to login user and return auth token."""
    response = await client.post(
        "/api/access/login",
        data={"username": user.email, "password": "testPassword123!"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 201
    return response.json()["access_token"]


async def _create_team_with_owner(session: AsyncSession, email_prefix: str = "owner") -> tuple[m.User, m.Team]:
    """Create a team with an owner user."""
    user = UserFactory.build(
        email=f"{email_prefix}-{uuid4().hex[:8]}@example.com",
        hashed_password=await get_password_hash("testPassword123!"),
        is_active=True,
        is_verified=True,
    )
    team = TeamFactory.build(
        name=f"Test Team {uuid4().hex[:8]}",
        slug=f"test-team-{uuid4().hex[:8]}",
    )
    session.add_all([user, team])
    await session.flush()

    membership = TeamMemberFactory.build(
        team_id=team.id,
        user_id=user.id,
        role=m.TeamRoles.ADMIN,
        is_owner=True,
    )
    session.add(membership)
    await session.commit()
    await session.refresh(team, ["members"])
    return user, team


async def _create_user(session: AsyncSession, email_prefix: str = "user") -> m.User:
    """Create a regular user."""
    user = UserFactory.build(
        email=f"{email_prefix}-{uuid4().hex[:8]}@example.com",
        hashed_password=await get_password_hash("testPassword123!"),
        is_active=True,
        is_verified=True,
    )
    session.add(user)
    await session.commit()
    return user


# --- Add Member Tests ---


@pytest.mark.anyio
async def test_add_member_success(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    """Test successful member addition to team."""
    owner, team = await _create_team_with_owner(session, "addmemowner")
    token = await _login_user(client, owner)

    # Create user to add
    new_member = await _create_user(session, "newmember")

    response = await client.post(
        f"/api/teams/{team.id}/members",
        json={"userName": new_member.email},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201
    data = response.json()
    # Verify team is returned with members
    assert "members" in data
    member_emails = [m["email"] for m in data["members"]]
    assert new_member.email in member_emails


@pytest.mark.anyio
async def test_add_member_already_member(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    """Test adding member who is already a member."""
    owner, team = await _create_team_with_owner(session, "dupmemowner")
    token = await _login_user(client, owner)

    # Try to add the owner (who is already a member)
    response = await client.post(
        f"/api/teams/{team.id}/members",
        json={"userName": owner.email},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 409
    assert "already a member" in response.text.lower()


@pytest.mark.anyio
async def test_add_member_user_not_found(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    """Test adding non-existent user as member."""
    owner, team = await _create_team_with_owner(session, "nofoundowner")
    token = await _login_user(client, owner)

    response = await client.post(
        f"/api/teams/{team.id}/members",
        json={"userName": "nonexistent@example.com"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404


@pytest.mark.anyio
async def test_add_member_unauthenticated(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    """Test adding member without authentication."""
    _, team = await _create_team_with_owner(session, "unauthaddowner")

    response = await client.post(
        f"/api/teams/{team.id}/members",
        json={"userName": "someone@example.com"},
    )

    assert response.status_code == 401


# --- Remove Member Tests ---


@pytest.mark.anyio
async def test_remove_member_success(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    """Test successful member removal from team."""
    owner, team = await _create_team_with_owner(session, "remowner")
    token = await _login_user(client, owner)

    # Create and add a member
    member = await _create_user(session, "removemember")

    # Add member first
    add_response = await client.post(
        f"/api/teams/{team.id}/members",
        json={"userName": member.email},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert add_response.status_code == 201

    # Remove the member (DELETE with json body requires request method)
    response = await client.request(
        "DELETE",
        f"/api/teams/{team.id}/members",
        json={"userName": member.email},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 202
    data = response.json()
    # Verify member is removed from team
    member_emails = [m["email"] for m in data["members"]]
    assert member.email not in member_emails


@pytest.mark.anyio
async def test_remove_member_not_a_member(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    """Test removing user who is not a member."""
    owner, team = await _create_team_with_owner(session, "notmemowner")
    token = await _login_user(client, owner)

    # Create user who is not a team member
    non_member = await _create_user(session, "nonmember")

    response = await client.request(
        "DELETE",
        f"/api/teams/{team.id}/members",
        json={"userName": non_member.email},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 409
    assert "not a member" in response.text.lower()


@pytest.mark.anyio
async def test_remove_member_user_not_found(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    """Test removing non-existent user."""
    owner, team = await _create_team_with_owner(session, "remnotfoundowner")
    token = await _login_user(client, owner)

    response = await client.request(
        "DELETE",
        f"/api/teams/{team.id}/members",
        json={"userName": "nonexistent@example.com"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404


@pytest.mark.anyio
async def test_remove_member_unauthenticated(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    """Test removing member without authentication."""
    _, team = await _create_team_with_owner(session, "unauthremowner")

    response = await client.request(
        "DELETE",
        f"/api/teams/{team.id}/members",
        json={"userName": "someone@example.com"},
    )

    assert response.status_code == 401


# --- Update Member Role Tests ---


@pytest.mark.anyio
async def test_update_member_role_success(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    """Test successful member role update."""
    owner, team = await _create_team_with_owner(session, "uproleowner")
    token = await _login_user(client, owner)

    # Create and add a member
    member = await _create_user(session, "roleupdate")

    # Add member first
    add_response = await client.post(
        f"/api/teams/{team.id}/members",
        json={"userName": member.email},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert add_response.status_code == 201

    # Update the member's role
    # Need to get the user_id from the member
    response = await client.patch(
        f"/api/teams/{team.id}/members/{member.id}",
        json={"role": "ADMIN"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "ADMIN"


@pytest.mark.anyio
async def test_update_member_role_not_a_member(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    """Test updating role for non-member."""
    owner, team = await _create_team_with_owner(session, "uprolenotmem")
    token = await _login_user(client, owner)

    # Create user who is not a team member
    non_member = await _create_user(session, "notroleupdate")

    response = await client.patch(
        f"/api/teams/{team.id}/members/{non_member.id}",
        json={"role": "ADMIN"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 409
    assert "not a member" in response.text.lower()


@pytest.mark.anyio
async def test_update_member_role_unauthenticated(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    """Test updating member role without authentication."""
    _, team = await _create_team_with_owner(session, "unauthuproleowner")
    random_user_id = uuid4()

    response = await client.patch(
        f"/api/teams/{team.id}/members/{random_user_id}",
        json={"role": "ADMIN"},
    )

    assert response.status_code == 401


@pytest.mark.anyio
async def test_update_member_role_invalid_role(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    """Test updating member with invalid role."""
    owner, team = await _create_team_with_owner(session, "invalidroleowner")
    token = await _login_user(client, owner)

    # Create and add a member
    member = await _create_user(session, "invalidrole")

    # Add member first
    add_response = await client.post(
        f"/api/teams/{team.id}/members",
        json={"userName": member.email},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert add_response.status_code == 201

    # Try to update with invalid role
    response = await client.patch(
        f"/api/teams/{team.id}/members/{member.id}",
        json={"role": "INVALID_ROLE"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 400


@pytest.mark.anyio
async def test_update_member_to_member_role(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    """Test updating member role to MEMBER (downgrade from ADMIN)."""
    owner, team = await _create_team_with_owner(session, "downgradeowner")
    token = await _login_user(client, owner)

    # Create and add a member as ADMIN
    member = await _create_user(session, "downgrademem")

    # Add member first
    add_response = await client.post(
        f"/api/teams/{team.id}/members",
        json={"userName": member.email},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert add_response.status_code == 201

    # Promote to ADMIN first
    await client.patch(
        f"/api/teams/{team.id}/members/{member.id}",
        json={"role": "ADMIN"},
        headers={"Authorization": f"Bearer {token}"},
    )

    # Downgrade to MEMBER
    response = await client.patch(
        f"/api/teams/{team.id}/members/{member.id}",
        json={"role": "MEMBER"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "MEMBER"

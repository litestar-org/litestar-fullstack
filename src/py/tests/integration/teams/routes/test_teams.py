"""Integration tests for team management endpoints.

This module combines tests from:
- test_team_endpoints.py (team CRUD and member operations)
- test_team_management.py (team lifecycle and permissions)
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

import pytest
from litestar_email import InMemoryBackend
from sqlalchemy import select

from app.db import models as m
from app.lib.crypt import get_password_hash
from tests.factories import TeamFactory, TeamMemberFactory, UserFactory, create_team_with_members, create_user_with_team

if TYPE_CHECKING:
    from httpx import AsyncClient
    from litestar.testing import AsyncTestClient
    from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = [pytest.mark.integration, pytest.mark.teams, pytest.mark.endpoints]


@pytest.fixture(autouse=True)
def clear_email_outbox() -> None:
    """Clear email outbox before each test."""
    InMemoryBackend.clear()


async def _login_user(client: AsyncClient, user: m.User, password: str = "testPassword123!") -> str:
    """Helper to login user and return auth token."""
    response = await client.post(
        "/api/access/login",
        data={"username": user.email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 201
    return response.json()["access_token"]


# =============================================================================
# Team CRUD Tests
# =============================================================================


@pytest.mark.anyio
async def test_create_team_success(authenticated_client: AsyncTestClient) -> None:
    """Test successful team creation."""
    team_data = {
        "name": "Test Team",
        "description": "A test team for integration testing",
    }

    response = await authenticated_client.post("/api/teams", json=team_data)

    assert response.status_code == 201
    team = response.json()
    assert team["name"] == "Test Team"
    assert team["description"] == "A test team for integration testing"
    assert team["slug"] is not None
    assert team["isActive"] is True


@pytest.mark.anyio
async def test_create_team_with_session(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    """Test successful team creation with database verification."""
    user = UserFactory.build(
        email="teamcreator@example.com",
        hashed_password=await get_password_hash("testPassword123!"),
        is_active=True,
        is_verified=True,
    )
    session.add(user)
    await session.commit()

    token = await _login_user(client, user)

    response = await client.post(
        "/api/teams",
        json={"name": "My New Test Team", "description": "A test team", "tags": ["development", "testing"]},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201
    response_data = response.json()
    assert response_data["name"] == "My New Test Team"
    assert response_data["description"] == "A test team"
    assert len(response_data["members"]) == 1
    assert response_data["members"][0]["email"] == user.email
    assert response_data["members"][0]["isOwner"] is True
    assert response_data["members"][0]["role"] == m.TeamRoles.ADMIN.value

    result = await session.execute(select(m.Team).where(m.Team.name == "My New Test Team"))
    team = result.scalar_one_or_none()
    assert team is not None
    membership_result = await session.execute(
        select(m.TeamMember).where(m.TeamMember.team_id == team.id, m.TeamMember.user_id == user.id)
    )
    membership = membership_result.scalar_one_or_none()
    assert membership is not None
    assert membership.is_owner is True
    assert membership.role == m.TeamRoles.ADMIN


@pytest.mark.anyio
async def test_create_team_unauthenticated(client: AsyncTestClient) -> None:
    """Test team creation without authentication fails."""
    team_data = {
        "name": "Test Team",
        "description": "A test team",
    }

    response = await client.post("/api/teams", json=team_data)

    assert response.status_code == 401


@pytest.mark.anyio
async def test_create_team_invalid_data(authenticated_client: AsyncTestClient) -> None:
    """Test team creation with invalid data."""
    team_data = {
        "description": "A test team without name",
    }

    response = await authenticated_client.post("/api/teams", json=team_data)

    assert response.status_code == 400


@pytest.mark.anyio
async def test_get_user_teams(
    authenticated_client: AsyncTestClient,
    test_user: m.User,
    test_team: m.Team,
) -> None:
    """Test getting user's teams."""
    response = await authenticated_client.get("/api/teams")

    assert response.status_code == 200
    teams_response = response.json()
    teams = teams_response["items"]
    assert len(teams) >= 1
    team_ids = [team["id"] for team in teams]
    assert str(test_team.id) in team_ids


@pytest.mark.anyio
async def test_get_user_teams_unauthenticated(client: AsyncTestClient) -> None:
    """Test getting teams without authentication fails."""
    response = await client.get("/api/teams")

    assert response.status_code == 401


@pytest.mark.anyio
async def test_list_teams_as_member(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    """Test listing teams where user is a member."""
    user, team1 = await create_user_with_team(session)

    other_user = UserFactory.build()
    other_team = TeamFactory.build()
    session.add_all([other_user, other_team])
    await session.flush()

    other_membership = TeamMemberFactory.build(
        team_id=other_team.id, user_id=other_user.id, role=m.TeamRoles.ADMIN, is_owner=True
    )
    session.add(other_membership)

    user.hashed_password = await get_password_hash("testPassword123!")
    await session.commit()

    token = await _login_user(client, user)

    response = await client.get("/api/teams", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    response_data = response.json()

    team_ids = [team["id"] for team in response_data["items"]]
    assert str(team1.id) in team_ids
    assert str(other_team.id) not in team_ids


@pytest.mark.anyio
async def test_get_team_details(
    authenticated_client: AsyncTestClient,
    test_team: m.Team,
) -> None:
    """Test getting team details."""
    response = await authenticated_client.get(f"/api/teams/{test_team.id}")

    assert response.status_code == 200
    team = response.json()
    assert team["id"] == str(test_team.id)
    assert team["name"] == test_team.name
    assert team["description"] == test_team.description


@pytest.mark.anyio
async def test_get_team_details_not_member(
    client: AsyncTestClient,
    test_team: m.Team,
    session: AsyncSession,
) -> None:
    """Test getting team details when not a member."""
    other_user = m.User(
        id=uuid4(),
        email="other@example.com",
        name="Other User",
        hashed_password=await get_password_hash("TestPassword123!"),
        is_active=True,
        is_verified=True,
    )
    session.add(other_user)
    await session.commit()

    login_response = await client.post(
        "/api/access/login", data={"username": other_user.email, "password": "TestPassword123!"}
    )

    if login_response.status_code == 201:
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.get(f"/api/teams/{test_team.id}", headers=headers)

        assert response.status_code in [403, 404]


@pytest.mark.anyio
async def test_get_team_details_nonexistent(authenticated_client: AsyncTestClient) -> None:
    """Test getting details for non-existent team."""
    response = await authenticated_client.get(f"/api/teams/{uuid4()}")

    assert response.status_code == 403


@pytest.mark.anyio
async def test_update_team(
    authenticated_client: AsyncTestClient,
    test_team: m.Team,
) -> None:
    """Test updating team information."""
    update_data = {
        "name": "Updated Team Name",
        "description": "Updated description",
    }

    response = await authenticated_client.patch(f"/api/teams/{test_team.id}", json=update_data)

    assert response.status_code == 200
    team = response.json()
    assert team["name"] == "Updated Team Name"
    assert team["description"] == "Updated description"


@pytest.mark.anyio
async def test_update_team_as_admin(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    """Test updating team as admin with database verification."""
    user, team = await create_user_with_team(session)
    user.hashed_password = await get_password_hash("testPassword123!")
    await session.commit()

    token = await _login_user(client, user)

    response = await client.patch(
        f"/api/teams/{team.id}",
        json={"name": "Updated Team Name", "description": "Updated description"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["name"] == "Updated Team Name"
    assert response_data["description"] == "Updated description"

    await session.refresh(team)
    assert team.name == "Updated Team Name"
    assert team.description == "Updated description"


@pytest.mark.anyio
async def test_update_team_as_member(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    """Test updating team as regular member (should fail)."""
    _owner, team = await create_user_with_team(session)

    member = UserFactory.build(
        hashed_password=await get_password_hash("testPassword123!"), is_active=True, is_verified=True
    )
    session.add(member)
    await session.flush()

    membership = TeamMemberFactory.build(team_id=team.id, user_id=member.id, role=m.TeamRoles.MEMBER, is_owner=False)
    session.add(membership)
    await session.commit()

    token = await _login_user(client, member)

    response = await client.patch(
        f"/api/teams/{team.id}",
        json={"name": "Should Not Update"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403


@pytest.mark.anyio
async def test_update_team_not_authorized(
    client: AsyncTestClient,
    test_team: m.Team,
    session: AsyncSession,
) -> None:
    """Test updating team when not authorized."""
    other_user = m.User(
        id=uuid4(),
        email="unauthorized@example.com",
        name="Unauthorized User",
        hashed_password=await get_password_hash("TestPassword123!"),
        is_active=True,
        is_verified=True,
    )
    session.add(other_user)
    await session.commit()

    login_response = await client.post(
        "/api/access/login", data={"username": other_user.email, "password": "TestPassword123!"}
    )

    if login_response.status_code == 201:
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        update_data = {"name": "Unauthorized Update"}

        response = await client.patch(f"/api/teams/{test_team.id}", json=update_data, headers=headers)

        assert response.status_code in [403, 404]


@pytest.mark.anyio
async def test_delete_team(
    authenticated_client: AsyncTestClient,
    test_team: m.Team,
) -> None:
    """Test deleting a team."""
    response = await authenticated_client.delete(f"/api/teams/{test_team.id}")

    assert response.status_code in [200, 204]


@pytest.mark.anyio
async def test_delete_team_as_admin(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    """Test deleting team as admin with database verification."""
    user, team = await create_user_with_team(session)
    user.hashed_password = await get_password_hash("testPassword123!")
    team_id = team.id
    await session.commit()

    token = await _login_user(client, user)

    response = await client.delete(f"/api/teams/{team_id}", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 204

    result = await session.execute(select(m.Team).where(m.Team.id == team_id))
    deleted_team = result.scalar_one_or_none()
    assert deleted_team is None


@pytest.mark.anyio
async def test_delete_team_not_owner(
    client: AsyncTestClient,
    test_team: m.Team,
    session: AsyncSession,
) -> None:
    """Test deleting team when not owner."""
    member_user = m.User(
        id=uuid4(),
        email="member@example.com",
        name="Member User",
        hashed_password=await get_password_hash("TestPassword123!"),
        is_active=True,
        is_verified=True,
    )
    session.add(member_user)
    await session.commit()

    membership = m.TeamMember(
        team_id=test_team.id,
        user_id=member_user.id,
        role=m.TeamRoles.MEMBER,
        is_owner=False,
    )
    session.add(membership)
    await session.commit()

    login_response = await client.post(
        "/api/access/login", data={"username": member_user.email, "password": "TestPassword123!"}
    )

    if login_response.status_code == 201:
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.delete(f"/api/teams/{test_team.id}", headers=headers)

        assert response.status_code == 403


# =============================================================================
# Team Member Tests
# =============================================================================


@pytest.mark.anyio
async def test_get_team_members(
    authenticated_client: AsyncTestClient,
    test_team: m.Team,
) -> None:
    """Test getting team members via team detail response."""
    response = await authenticated_client.get(f"/api/teams/{test_team.id}")

    assert response.status_code == 200
    team = response.json()
    members = team.get("members", [])
    assert len(members) >= 1


@pytest.mark.anyio
async def test_add_team_member(
    authenticated_client: AsyncTestClient,
    test_team: m.Team,
    session: AsyncSession,
) -> None:
    """Test adding a team member."""
    new_member = m.User(
        id=uuid4(),
        email="newmember@example.com",
        name="New Member",
        hashed_password=await get_password_hash("TestPassword123!"),
        is_active=True,
        is_verified=True,
    )
    session.add(new_member)
    await session.commit()

    member_data = {
        "userName": new_member.email,
    }

    response = await authenticated_client.post(f"/api/teams/{test_team.id}/members", json=member_data)

    assert response.status_code == 201
    team = response.json()
    assert "id" in team
    member_emails = [member.get("email") or member.get("user", {}).get("email") for member in team.get("members", [])]
    assert new_member.email in member_emails


@pytest.mark.anyio
async def test_add_member_to_team_success(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    """Test successfully adding a member to a team with database verification."""
    owner, team = await create_user_with_team(session)
    owner.hashed_password = await get_password_hash("testPassword123!")

    new_member = UserFactory.build(email="newmember@example.com", is_active=True, is_verified=True)
    session.add(new_member)
    await session.commit()

    token = await _login_user(client, owner)

    response = await client.post(
        f"/api/teams/{team.id}/members",
        json={"userName": "newmember@example.com"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201
    response_data = response.json()

    member_emails = [
        member.get("user", {}).get("email") or member.get("email") for member in response_data.get("members", [])
    ]
    assert "newmember@example.com" in member_emails

    result = await session.execute(
        select(m.TeamMember).where(m.TeamMember.team_id == team.id, m.TeamMember.user_id == new_member.id)
    )
    membership = result.scalar_one_or_none()
    assert membership is not None
    assert membership.role == m.TeamRoles.MEMBER


@pytest.mark.anyio
async def test_add_member_already_exists(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    """Test adding a member who is already in the team."""
    team, members = await create_team_with_members(session, member_count=2)
    owner = members[0]
    existing_member = members[1]

    owner.hashed_password = await get_password_hash("testPassword123!")
    await session.commit()

    token = await _login_user(client, owner)

    response = await client.post(
        f"/api/teams/{team.id}/members",
        json={"userName": existing_member.email},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code in {409, 500}


@pytest.mark.anyio
async def test_add_member_nonexistent_user(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    """Test adding a non-existent user to a team."""
    owner, team = await create_user_with_team(session)
    owner.hashed_password = await get_password_hash("testPassword123!")
    await session.commit()

    token = await _login_user(client, owner)

    response = await client.post(
        f"/api/teams/{team.id}/members",
        json={"userName": "nonexistent@example.com"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code in {404, 500}


@pytest.mark.anyio
async def test_remove_team_member(
    authenticated_client: AsyncTestClient,
    test_team: m.Team,
    session: AsyncSession,
) -> None:
    """Test removing a team member."""
    member_to_remove = m.User(
        id=uuid4(),
        email="removeme@example.com",
        name="Remove Me",
        hashed_password=await get_password_hash("TestPassword123!"),
        is_active=True,
        is_verified=True,
    )
    session.add(member_to_remove)
    await session.commit()

    membership = m.TeamMember(
        team_id=test_team.id,
        user_id=member_to_remove.id,
        role=m.TeamRoles.MEMBER,
        is_owner=False,
    )
    session.add(membership)
    await session.commit()

    response = await authenticated_client.request(
        "DELETE",
        f"/api/teams/{test_team.id}/members",
        json={"userName": member_to_remove.email},
    )

    assert response.status_code == 202


@pytest.mark.anyio
async def test_remove_member_from_team_success(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    """Test successfully removing a member from a team with database verification."""
    team, members = await create_team_with_members(session, member_count=3)
    owner = members[0]
    member_to_remove = members[1]

    owner.hashed_password = await get_password_hash("testPassword123!")
    await session.commit()

    token = await _login_user(client, owner)

    response = await client.request(
        "DELETE",
        f"/api/teams/{team.id}/members",
        json={"userName": member_to_remove.email},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 202
    response_data = response.json()

    member_emails = [member["email"] for member in response_data["members"]]
    assert member_to_remove.email not in member_emails

    result = await session.execute(
        select(m.TeamMember).where(m.TeamMember.team_id == team.id, m.TeamMember.user_id == member_to_remove.id)
    )
    membership = result.scalar_one_or_none()
    assert membership is None


@pytest.mark.anyio
async def test_update_member_role(
    authenticated_client: AsyncTestClient,
    test_team: m.Team,
    session: AsyncSession,
) -> None:
    """Test updating a team member's role."""
    member_user = m.User(
        id=uuid4(),
        email="promoteme@example.com",
        name="Promote Me",
        hashed_password=await get_password_hash("TestPassword123!"),
        is_active=True,
        is_verified=True,
    )
    session.add(member_user)
    await session.commit()

    membership = m.TeamMember(
        team_id=test_team.id,
        user_id=member_user.id,
        role=m.TeamRoles.MEMBER,
        is_owner=False,
    )
    session.add(membership)
    await session.commit()

    update_data = {"role": m.TeamRoles.ADMIN.value}

    response = await authenticated_client.patch(f"/api/teams/{test_team.id}/members/{member_user.id}", json=update_data)

    assert response.status_code == 200
    membership = response.json()
    assert membership["role"] == m.TeamRoles.ADMIN.value


# =============================================================================
# Team Invitation Tests
# =============================================================================


@pytest.mark.anyio
async def test_invite_team_member(
    authenticated_client: AsyncTestClient,
    test_team: m.Team,
) -> None:
    """Test inviting a team member."""
    invitation_data = {
        "email": "newmember@example.com",
        "role": m.TeamRoles.MEMBER.value,
    }

    response = await authenticated_client.post(
        f"/api/teams/{test_team.id}/invitations",
        json=invitation_data,
    )

    assert response.status_code == 201
    invitation = response.json()
    assert invitation["email"] == "newmember@example.com"
    assert invitation["role"] == m.TeamRoles.MEMBER.value
    assert invitation["isAccepted"] is False

    assert len(InMemoryBackend.outbox) == 1
    assert "newmember@example.com" in InMemoryBackend.outbox[0].to


@pytest.mark.anyio
async def test_invite_existing_member(
    authenticated_client: AsyncTestClient,
    test_team: m.Team,
    test_user: m.User,
) -> None:
    """Test inviting someone who is already a member."""
    invitation_data = {
        "email": test_user.email,
        "role": m.TeamRoles.MEMBER.value,
    }

    response = await authenticated_client.post(f"/api/teams/{test_team.id}/invitations", json=invitation_data)

    assert response.status_code == 400


@pytest.mark.anyio
async def test_get_team_invitations(
    authenticated_client: AsyncTestClient,
    test_team: m.Team,
    test_team_invitation: m.TeamInvitation,
) -> None:
    """Test getting team invitations."""
    response = await authenticated_client.get(f"/api/teams/{test_team.id}/invitations")

    assert response.status_code == 200
    response_data = response.json()
    invitations = response_data["items"]
    assert len(invitations) >= 1
    invitation_emails = [inv["email"] for inv in invitations]
    assert test_team_invitation.email in invitation_emails


@pytest.mark.anyio
async def test_accept_team_invitation(
    client: AsyncTestClient,
    test_team_invitation: m.TeamInvitation,
    session: AsyncSession,
) -> None:
    """Test accepting a team invitation."""
    invited_user = m.User(
        id=uuid4(),
        email=test_team_invitation.email,
        name="Invited User",
        hashed_password=await get_password_hash("TestPassword123!"),
        is_active=True,
        is_verified=True,
    )
    session.add(invited_user)
    await session.commit()

    login_response = await client.post(
        "/api/access/login", data={"username": invited_user.email, "password": "TestPassword123!"}
    )
    assert login_response.status_code == 201
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.post(
        f"/api/teams/{test_team_invitation.team_id}/invitations/{test_team_invitation.id}/accept",
        headers=headers,
    )

    assert response.status_code == 201
    result = response.json()
    assert "accepted" in result["message"].lower() or "joined" in result["message"].lower()


@pytest.mark.anyio
async def test_reject_team_invitation(
    client: AsyncTestClient,
    test_team_invitation: m.TeamInvitation,
    session: AsyncSession,
) -> None:
    """Test rejecting a team invitation."""
    invited_user = m.User(
        id=uuid4(),
        email=test_team_invitation.email,
        name="Invited User",
        hashed_password=await get_password_hash("TestPassword123!"),
        is_active=True,
        is_verified=True,
    )
    session.add(invited_user)
    await session.commit()

    login_response = await client.post(
        "/api/access/login",
        data={"username": invited_user.email, "password": "TestPassword123!"},
    )
    assert login_response.status_code == 201
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.post(
        f"/api/teams/{test_team_invitation.team_id}/invitations/{test_team_invitation.id}/reject",
        headers=headers,
    )

    assert response.status_code == 201
    result = response.json()
    assert "rejected" in result["message"].lower() or "declined" in result["message"].lower()


@pytest.mark.anyio
async def test_cancel_team_invitation(
    authenticated_client: AsyncTestClient,
    test_team_invitation: m.TeamInvitation,
) -> None:
    """Test canceling a team invitation."""
    response = await authenticated_client.delete(
        f"/api/teams/{test_team_invitation.team_id}/invitations/{test_team_invitation.id}"
    )

    assert response.status_code in [200, 204]


# =============================================================================
# Permission Tests
# =============================================================================


@pytest.mark.anyio
async def test_team_owner_permissions(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    """Test that team owners have all permissions."""
    owner, team = await create_user_with_team(session)
    owner.hashed_password = await get_password_hash("testPassword123!")
    await session.commit()

    token = await _login_user(client, owner)

    response = await client.get(f"/api/teams/{team.id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200

    response = await client.patch(
        f"/api/teams/{team.id}", json={"name": "Updated by Owner"}, headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200

    response = await client.delete(f"/api/teams/{team.id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 204


@pytest.mark.anyio
async def test_team_admin_permissions(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    """Test that team admins have appropriate permissions."""
    _owner, team = await create_user_with_team(session)

    admin = UserFactory.build(
        hashed_password=await get_password_hash("testPassword123!"), is_active=True, is_verified=True
    )
    session.add(admin)
    await session.flush()

    admin_membership = TeamMemberFactory.build(
        team_id=team.id, user_id=admin.id, role=m.TeamRoles.ADMIN, is_owner=False
    )
    session.add(admin_membership)
    await session.commit()

    token = await _login_user(client, admin)

    response = await client.get(f"/api/teams/{team.id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200

    response = await client.patch(
        f"/api/teams/{team.id}", json={"name": "Updated by Admin"}, headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200

    response = await client.delete(f"/api/teams/{team.id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


@pytest.mark.anyio
async def test_team_member_permissions(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    """Test that team members have limited permissions."""
    _owner, team = await create_user_with_team(session)

    member = UserFactory.build(
        hashed_password=await get_password_hash("testPassword123!"), is_active=True, is_verified=True
    )
    session.add(member)
    await session.flush()

    member_membership = TeamMemberFactory.build(
        team_id=team.id, user_id=member.id, role=m.TeamRoles.MEMBER, is_owner=False
    )
    session.add(member_membership)
    await session.commit()

    token = await _login_user(client, member)

    response = await client.get(f"/api/teams/{team.id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200

    response = await client.patch(
        f"/api/teams/{team.id}",
        json={"name": "Unauthorized Update"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403

    response = await client.delete(f"/api/teams/{team.id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


@pytest.mark.anyio
async def test_non_member_permissions(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    """Test that non-members have no access to team."""
    _owner, team = await create_user_with_team(session)

    non_member = UserFactory.build(
        hashed_password=await get_password_hash("testPassword123!"), is_active=True, is_verified=True
    )
    session.add(non_member)
    await session.commit()

    token = await _login_user(client, non_member)

    response = await client.get(f"/api/teams/{team.id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403

    response = await client.patch(
        f"/api/teams/{team.id}",
        json={"name": "Unauthorized Update"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403

    response = await client.delete(f"/api/teams/{team.id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


# =============================================================================
# Seeded Data Tests
# =============================================================================


@pytest.mark.anyio
async def test_teams_with_no_auth(client: AsyncTestClient) -> None:
    response = await client.patch("/api/teams/97108ac1-ffcb-411d-8b1e-d9183399f63b", json={"name": "TEST UPDATE"})
    assert response.status_code == 401
    response = await client.post(
        "/api/teams/",
        json={"name": "A User", "email": "new-user@example.com", "password": "S3cret!"},
    )
    assert response.status_code == 401
    response = await client.get("/api/teams/97108ac1-ffcb-411d-8b1e-d9183399f63b")
    assert response.status_code == 401
    response = await client.get("/api/teams")
    assert response.status_code == 401
    response = await client.delete("/api/teams/97108ac1-ffcb-411d-8b1e-d9183399f63b")
    assert response.status_code == 401


@pytest.mark.anyio
async def test_teams_with_incorrect_role(
    client: AsyncTestClient,
    user_token_headers: dict[str, str],
    seeded_db: None,
) -> None:
    response = await client.patch(
        "/api/teams/81108ac1-ffcb-411d-8b1e-d91833999999",
        json={"name": "TEST UPDATE"},
        headers=user_token_headers,
    )
    assert response.status_code == 403
    response = await client.post(
        "/api/teams/",
        json={"name": "A new team."},
        headers=user_token_headers,
    )
    assert response.status_code == 201
    response = await client.get("/api/teams/81108ac1-ffcb-411d-8b1e-d91833999999", headers=user_token_headers)
    assert response.status_code == 403
    response = await client.get("/api/teams", headers=user_token_headers)
    assert response.status_code == 200
    response = await client.delete("/api/teams/81108ac1-ffcb-411d-8b1e-d91833999999", headers=user_token_headers)
    assert response.status_code == 403


@pytest.mark.anyio
async def test_teams_list(
    client: AsyncTestClient,
    superuser_token_headers: dict[str, str],
    seeded_db: None,
) -> None:
    response = await client.get("/api/teams", headers=superuser_token_headers)
    assert response.status_code == 200
    assert int(response.json()["total"]) > 0


@pytest.mark.anyio
async def test_teams_get(
    client: AsyncTestClient,
    superuser_token_headers: dict[str, str],
    seeded_db: None,
) -> None:
    response = await client.get("/api/teams/97108ac1-ffcb-411d-8b1e-d9183399f63b", headers=superuser_token_headers)
    assert response.status_code == 200
    assert response.json()["name"] == "Test Team"


@pytest.mark.anyio
async def test_teams_create(
    client: AsyncTestClient,
    superuser_token_headers: dict[str, str],
    seeded_db: None,
) -> None:
    response = await client.post(
        "/api/teams/",
        json={"name": "My First Team", "tags": ["cool tag"]},
        headers=superuser_token_headers,
    )
    assert response.status_code == 201


@pytest.mark.anyio
async def test_teams_update(
    client: AsyncTestClient,
    superuser_token_headers: dict[str, str],
    seeded_db: None,
) -> None:
    response = await client.patch(
        "/api/teams/97108ac1-ffcb-411d-8b1e-d9183399f63b",
        json={"name": "Name Changed"},
        headers=superuser_token_headers,
    )
    assert response.status_code == 200


@pytest.mark.anyio
async def test_teams_delete(
    client: AsyncTestClient,
    superuser_token_headers: dict[str, str],
    seeded_db: None,
) -> None:
    response = await client.delete(
        "/api/teams/81108ac1-ffcb-411d-8b1e-d91833999999",
        headers=superuser_token_headers,
    )
    assert response.status_code == 204
    response = await client.get(
        "/api/users/5ef29f3c-3560-4d15-ba6b-a2e5c721e999",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200


@pytest.mark.anyio
async def test_teams_add_remove_member(
    client: AsyncTestClient,
    superuser_token_headers: dict[str, str],
    seeded_db: None,
) -> None:
    response = await client.post(
        "/api/teams/81108ac1-ffcb-411d-8b1e-d91833999999/members",
        headers=superuser_token_headers,
        json={"userName": "user@example.com"},
    )
    assert response.status_code == 201
    assert "user@example.com" in [e["email"] for e in response.json()["members"]]

    response = await client.request(
        "DELETE",
        "/api/teams/81108ac1-ffcb-411d-8b1e-d91833999999/members",
        headers=superuser_token_headers,
        json={"userName": "user@example.com"},
    )
    assert response.status_code == 202
    assert "user@example.com" not in [e["email"] for e in response.json()["members"]]


@pytest.mark.anyio
async def test_tags_list(
    client: AsyncTestClient,
    superuser_token_headers: dict[str, str],
    seeded_db: None,
) -> None:
    response = await client.get("/api/tags", headers=superuser_token_headers)
    resj = response.json()
    assert response.status_code == 200
    assert int(resj["total"]) >= 3


# =============================================================================
# Lifecycle Tests
# =============================================================================


@pytest.mark.anyio
async def test_complete_team_lifecycle(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    """Test complete team creation, management, and deletion workflow."""
    owner = UserFactory.build(
        email="owner@example.com",
        hashed_password=await get_password_hash("testPassword123!"),
        is_active=True,
        is_verified=True,
    )
    member1 = UserFactory.build(email="member1@example.com", is_active=True, is_verified=True)
    member2 = UserFactory.build(email="member2@example.com", is_active=True, is_verified=True)
    session.add_all([owner, member1, member2])
    await session.commit()

    token = await _login_user(client, owner)

    response = await client.post(
        "/api/teams",
        json={"name": "Full Lifecycle Team", "description": "Test team for complete workflow"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    team_data = response.json()
    team_id = team_data["id"]

    response = await client.post(
        f"/api/teams/{team_id}/members",
        json={"userName": "member1@example.com"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201

    response = await client.post(
        f"/api/teams/{team_id}/members",
        json={"userName": "member2@example.com"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201

    response = await client.get(f"/api/teams/{team_id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    team_data = response.json()
    assert len(team_data["members"]) == 3

    response = await client.patch(
        f"/api/teams/{team_id}",
        json={"name": "Updated Lifecycle Team", "description": "Updated description"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200

    response = await client.request(
        "DELETE",
        f"/api/teams/{team_id}/members",
        json={"userName": "member2@example.com"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 202

    response = await client.get(f"/api/teams/{team_id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    team_data = response.json()
    assert len(team_data["members"]) == 2
    member_emails = [member.get("user", {}).get("email") or member.get("email") for member in team_data["members"]]
    assert "member2@example.com" not in member_emails

    response = await client.delete(f"/api/teams/{team_id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 204

    response = await client.get(f"/api/teams/{team_id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code in {403, 404}


@pytest.mark.anyio
async def test_team_security_isolation(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    """Test that team data is properly isolated between teams."""
    owner1, team1 = await create_user_with_team(session)
    owner2, team2 = await create_user_with_team(session)

    owner1.hashed_password = await get_password_hash("testPassword123!")
    owner2.hashed_password = await get_password_hash("testPassword123!")
    await session.commit()

    token1 = await _login_user(client, owner1)
    token2 = await _login_user(client, owner2)

    response = await client.get("/api/teams", headers={"Authorization": f"Bearer {token1}"})
    assert response.status_code == 200
    teams_data = response.json()
    team_ids = [team["id"] for team in teams_data["items"]]
    assert str(team1.id) in team_ids
    assert str(team2.id) not in team_ids

    response = await client.get("/api/teams", headers={"Authorization": f"Bearer {token2}"})
    assert response.status_code == 200
    teams_data = response.json()
    team_ids = [team["id"] for team in teams_data["items"]]
    assert str(team2.id) in team_ids
    assert str(team1.id) not in team_ids

    response = await client.get(f"/api/teams/{team2.id}", headers={"Authorization": f"Bearer {token1}"})
    assert response.status_code == 403

    response = await client.get(f"/api/teams/{team1.id}", headers={"Authorization": f"Bearer {token2}"})
    assert response.status_code == 403

"""Integration tests for team management endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, patch

import pytest

from app.db import models as m

if TYPE_CHECKING:
    from litestar.testing import AsyncTestClient
    from sqlalchemy.ext.asyncio import AsyncSession


pytestmark = [pytest.mark.integration, pytest.mark.teams, pytest.mark.endpoints]


class TestTeamEndpoints:
    """Test team management API endpoints."""

    @pytest.mark.asyncio
    async def test_create_team_success(self, authenticated_client: AsyncTestClient) -> None:
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

    @pytest.mark.asyncio
    async def test_create_team_unauthenticated(self, client: AsyncTestClient) -> None:
        """Test team creation without authentication fails."""
        team_data = {
            "name": "Test Team",
            "description": "A test team",
        }

        response = await client.post("/api/teams", json=team_data)

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_team_invalid_data(self, authenticated_client: AsyncTestClient) -> None:
        """Test team creation with invalid data."""
        # Missing required name field
        team_data = {
            "description": "A test team without name",
        }

        response = await authenticated_client.post("/api/teams", json=team_data)

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_get_user_teams(
        self,
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

    @pytest.mark.asyncio
    async def test_get_user_teams_unauthenticated(self, client: AsyncTestClient) -> None:
        """Test getting teams without authentication fails."""
        response = await client.get("/api/teams")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_team_details(
        self,
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

    @pytest.mark.asyncio
    async def test_get_team_details_not_member(
        self,
        client: AsyncTestClient,
        test_team: m.Team,
        session: AsyncSession,
    ) -> None:
        """Test getting team details when not a member."""
        # Create a different user
        from uuid import uuid4

        from app.lib.crypt import get_password_hash

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

        # Login as the other user
        login_response = await client.post(
            "/api/access/login", data={"username": other_user.email, "password": "TestPassword123!"}
        )

        if login_response.status_code == 200:
            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            response = await client.get(f"/api/teams/{test_team.id}", headers=headers)

            # Should either be forbidden or not found depending on implementation
            assert response.status_code in [403, 404]

    @pytest.mark.asyncio
    async def test_get_team_details_nonexistent(self, authenticated_client: AsyncTestClient) -> None:
        """Test getting details for non-existent team."""
        from uuid import uuid4

        response = await authenticated_client.get(f"/api/teams/{uuid4()}")

        # Should return 403 (security by obscurity - don't reveal if team exists)
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_update_team(
        self,
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

    @pytest.mark.asyncio
    async def test_update_team_not_authorized(
        self,
        client: AsyncTestClient,
        test_team: m.Team,
        session: AsyncSession,
    ) -> None:
        """Test updating team when not authorized."""
        # Create a different user who is not a team member
        from uuid import uuid4

        from app.lib.crypt import get_password_hash

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

        # Login as the unauthorized user
        login_response = await client.post(
            "/api/access/login", data={"username": other_user.email, "password": "TestPassword123!"}
        )

        if login_response.status_code == 200:
            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            update_data = {"name": "Unauthorized Update"}

            response = await client.patch(f"/api/teams/{test_team.id}", json=update_data, headers=headers)

            assert response.status_code in [403, 404]

    @pytest.mark.asyncio
    async def test_delete_team(
        self,
        authenticated_client: AsyncTestClient,
        test_team: m.Team,
    ) -> None:
        """Test deleting a team."""
        response = await authenticated_client.delete(f"/api/teams/{test_team.id}")

        assert response.status_code in [200, 204]

    @pytest.mark.asyncio
    async def test_delete_team_not_owner(
        self,
        client: AsyncTestClient,
        test_team: m.Team,
        session: AsyncSession,
    ) -> None:
        """Test deleting team when not owner."""
        # Create a different user
        from uuid import uuid4

        from app.lib.crypt import get_password_hash

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

        # Add user as regular member (not owner)
        from app.db.models.team_member import TeamMember
        from app.db.models.team_roles import TeamRoles

        membership = TeamMember(
            team_id=test_team.id,
            user_id=member_user.id,
            role=TeamRoles.MEMBER,
            is_owner=False,
        )
        session.add(membership)
        await session.commit()

        # Login as the member
        login_response = await client.post(
            "/api/access/login", data={"username": member_user.email, "password": "TestPassword123!"}
        )

        if login_response.status_code == 200:
            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            response = await client.delete(f"/api/teams/{test_team.id}", headers=headers)

            assert response.status_code == 403


class TestTeamMemberEndpoints:
    """Test team member management endpoints."""

    @pytest.mark.asyncio
    async def test_get_team_members(
        self,
        authenticated_client: AsyncTestClient,
        test_team: m.Team,
    ) -> None:
        """Test getting team members."""
        response = await authenticated_client.get(f"/api/teams/{test_team.id}/members")

        assert response.status_code == 200
        members = response.json()
        assert len(members) >= 1  # At least the owner

        # Check owner is present
        owner_roles = [member["role"] for member in members if member.get("is_owner")]
        assert len(owner_roles) >= 1

    @pytest.mark.asyncio
    async def test_get_team_members_not_member(
        self,
        client: AsyncTestClient,
        test_team: m.Team,
        session: AsyncSession,
    ) -> None:
        """Test getting team members when not a member."""
        # Create a different user
        from uuid import uuid4

        from app.lib.crypt import get_password_hash

        other_user = m.User(
            id=uuid4(),
            email="outsider@example.com",
            name="Outsider User",
            hashed_password=await get_password_hash("TestPassword123!"),
            is_active=True,
            is_verified=True,
        )
        session.add(other_user)
        await session.commit()

        # Login as the outsider
        login_response = await client.post(
            "/api/access/login", data={"username": other_user.email, "password": "TestPassword123!"}
        )

        if login_response.status_code == 200:
            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            response = await client.get(f"/api/teams/{test_team.id}/members", headers=headers)

            assert response.status_code in [403, 404]

    @pytest.mark.asyncio
    async def test_add_team_member(
        self,
        authenticated_client: AsyncTestClient,
        test_team: m.Team,
        session: AsyncSession,
    ) -> None:
        """Test adding a team member."""
        # Create a user to add
        from uuid import uuid4

        from app.lib.crypt import get_password_hash

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
            "user_id": str(new_member.id),
            "role": "member",
        }

        response = await authenticated_client.post(f"/api/teams/{test_team.id}/members", json=member_data)

        assert response.status_code == 201
        membership = response.json()
        assert membership["user_id"] == str(new_member.id)
        assert membership["role"] == "member"
        assert membership["is_active"] is True

    @pytest.mark.asyncio
    async def test_add_team_member_not_admin(
        self,
        client: AsyncTestClient,
        test_team: m.Team,
        session: AsyncSession,
    ) -> None:
        """Test adding team member when not admin."""
        # Create two users
        from uuid import uuid4

        from app.lib.crypt import get_password_hash

        member_user = m.User(
            id=uuid4(),
            email="member@example.com",
            name="Member User",
            hashed_password=await get_password_hash("TestPassword123!"),
            is_active=True,
            is_verified=True,
        )

        target_user = m.User(
            id=uuid4(),
            email="target@example.com",
            name="Target User",
            hashed_password=await get_password_hash("TestPassword123!"),
            is_active=True,
            is_verified=True,
        )

        session.add_all([member_user, target_user])
        await session.commit()

        # Add first user as regular member
        from app.db.models.team_member import TeamMember
        from app.db.models.team_roles import TeamRoles

        membership = TeamMember(
            team_id=test_team.id,
            user_id=member_user.id,
            role=TeamRoles.MEMBER,
            is_owner=False,
        )
        session.add(membership)
        await session.commit()

        # Login as the regular member
        login_response = await client.post(
            "/api/access/login", data={"username": member_user.email, "password": "TestPassword123!"}
        )

        if login_response.status_code == 200:
            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            member_data = {
                "user_id": str(target_user.id),
                "role": "member",
            }

            response = await client.post(f"/api/teams/{test_team.id}/members", json=member_data, headers=headers)

            assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_remove_team_member(
        self,
        authenticated_client: AsyncTestClient,
        test_team: m.Team,
        session: AsyncSession,
    ) -> None:
        """Test removing a team member."""
        # Create a member to remove
        from uuid import uuid4

        from app.lib.crypt import get_password_hash

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

        # Add them to the team
        from app.db.models.team_member import TeamMember
        from app.db.models.team_roles import TeamRoles

        membership = TeamMember(
            team_id=test_team.id,
            user_id=member_to_remove.id,
            role=TeamRoles.MEMBER,
            is_owner=False,
        )
        session.add(membership)
        await session.commit()

        # Remove the member
        response = await authenticated_client.delete(f"/api/teams/{test_team.id}/members/{member_to_remove.id}")

        assert response.status_code in [200, 204]

    @pytest.mark.asyncio
    async def test_update_member_role(
        self,
        authenticated_client: AsyncTestClient,
        test_team: m.Team,
        session: AsyncSession,
    ) -> None:
        """Test updating a team member's role."""
        # Create a member
        from uuid import uuid4

        from app.lib.crypt import get_password_hash

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

        # Add them to the team as member
        from app.db.models.team_member import TeamMember
        from app.db.models.team_roles import TeamRoles

        membership = TeamMember(
            team_id=test_team.id,
            user_id=member_user.id,
            role=TeamRoles.MEMBER,
            is_owner=False,
        )
        session.add(membership)
        await session.commit()

        # Update their role
        update_data = {"role": m.TeamRoles.ADMIN.value}

        response = await authenticated_client.patch(
            f"/api/teams/{test_team.id}/members/{member_user.id}", json=update_data
        )

        assert response.status_code == 200
        membership = response.json()
        assert membership["role"] == m.TeamRoles.ADMIN.value


class TestTeamInvitationEndpoints:
    """Test team invitation endpoints."""

    @pytest.mark.asyncio
    async def test_invite_team_member(
        self,
        authenticated_client: AsyncTestClient,
        test_team: m.Team,
    ) -> None:
        """Test inviting a team member."""
        with patch("app.lib.email.email_service.send_team_invitation_email", new_callable=AsyncMock) as mock_send:
            mock_send.return_value = True

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

            # Verify invitation email was sent
            mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_invite_existing_member(
        self,
        authenticated_client: AsyncTestClient,
        test_team: m.Team,
        test_user: m.User,
    ) -> None:
        """Test inviting someone who is already a member."""
        invitation_data = {
            "email": test_user.email,  # User is already team owner
            "role": m.TeamRoles.MEMBER.value,
        }

        response = await authenticated_client.post(f"/api/teams/{test_team.id}/invitations", json=invitation_data)

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_get_team_invitations(
        self,
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

    @pytest.mark.asyncio
    async def test_accept_team_invitation(
        self,
        client: AsyncTestClient,
        test_team_invitation: m.TeamInvitation,
        session: AsyncSession,
    ) -> None:
        """Test accepting a team invitation."""
        # Create a user with the invitation email
        from uuid import uuid4

        from app.lib.crypt import get_password_hash

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

        # Login as the invited user
        login_response = await client.post(
            "/api/access/login", data={"username": invited_user.email, "password": "TestPassword123!"}
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.post(
            f"/api/teams/{test_team_invitation.team_id}/invitations/{test_team_invitation.id}/accept",
            headers=headers,
        )

        assert response.status_code == 200
        result = response.json()
        assert "accepted" in result["message"].lower() or "joined" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_reject_team_invitation(
        self,
        client: AsyncTestClient,
        test_team_invitation: m.TeamInvitation,
        session: AsyncSession,
    ) -> None:
        """Test rejecting a team invitation."""
        from uuid import uuid4

        from app.lib.crypt import get_password_hash

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
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.post(
            f"/api/teams/{test_team_invitation.team_id}/invitations/{test_team_invitation.id}/reject",
            headers=headers,
        )

        assert response.status_code == 200
        result = response.json()
        assert "rejected" in result["message"].lower() or "declined" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_cancel_team_invitation(
        self,
        authenticated_client: AsyncTestClient,
        test_team_invitation: m.TeamInvitation,
    ) -> None:
        """Test canceling a team invitation."""
        response = await authenticated_client.delete(
            f"/api/teams/{test_team_invitation.team_id}/invitations/{test_team_invitation.id}"
        )

        assert response.status_code in [200, 204]

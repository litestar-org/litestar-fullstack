"""Comprehensive tests for team domain guards."""

from __future__ import annotations

from unittest.mock import Mock
from uuid import uuid4

import pytest
from litestar.exceptions import PermissionDeniedException

from app.db import models as m
from app.domain.teams.guards import (
    requires_team_admin,
    requires_team_membership,
    requires_team_ownership,
)
from app.lib import constants

pytestmark = [pytest.mark.unit, pytest.mark.auth, pytest.mark.security, pytest.mark.teams]


def test_membership_superuser_flag_passes() -> None:
    """Test that is_superuser=True passes the guard."""
    team_id = uuid4()

    mock_user = Mock()
    mock_user.is_superuser = True
    mock_user.roles = []
    mock_user.teams = []

    mock_connection = Mock()
    mock_connection.user = mock_user
    mock_connection.path_params = {"team_id": team_id}
    mock_handler = Mock()

    # Should not raise
    requires_team_membership(mock_connection, mock_handler)


def test_membership_superuser_role_passes() -> None:
    """Test that user with SUPERUSER_ACCESS_ROLE passes."""
    team_id = uuid4()

    mock_role = Mock()
    mock_role.role_name = constants.SUPERUSER_ACCESS_ROLE

    mock_user = Mock()
    mock_user.is_superuser = False
    mock_user.roles = [mock_role]
    mock_user.teams = []

    mock_connection = Mock()
    mock_connection.user = mock_user
    mock_connection.path_params = {"team_id": team_id}
    mock_handler = Mock()

    # Should not raise
    requires_team_membership(mock_connection, mock_handler)


def test_team_member_passes() -> None:
    """Test that team member passes the guard."""
    team_id = uuid4()

    mock_team = Mock()
    mock_team.id = team_id

    mock_membership = Mock()
    mock_membership.team = mock_team

    mock_user = Mock()
    mock_user.is_superuser = False
    mock_user.roles = []
    mock_user.teams = [mock_membership]

    mock_connection = Mock()
    mock_connection.user = mock_user
    mock_connection.path_params = {"team_id": team_id}
    mock_handler = Mock()

    # Should not raise
    requires_team_membership(mock_connection, mock_handler)


def test_non_member_raises_permission_denied() -> None:
    """Test that non-member raises PermissionDeniedException."""
    team_id = uuid4()
    other_team_id = uuid4()

    mock_team = Mock()
    mock_team.id = other_team_id  # Different team

    mock_membership = Mock()
    mock_membership.team = mock_team

    mock_user = Mock()
    mock_user.is_superuser = False
    mock_user.roles = []
    mock_user.teams = [mock_membership]

    mock_connection = Mock()
    mock_connection.user = mock_user
    mock_connection.path_params = {"team_id": team_id}
    mock_handler = Mock()

    with pytest.raises(PermissionDeniedException) as exc_info:
        requires_team_membership(mock_connection, mock_handler)

    assert "Insufficient permissions" in str(exc_info.value.detail)


def test_no_teams_raises_permission_denied() -> None:
    """Test that user with no teams raises PermissionDeniedException."""
    team_id = uuid4()

    mock_user = Mock()
    mock_user.is_superuser = False
    mock_user.roles = []
    mock_user.teams = []

    mock_connection = Mock()
    mock_connection.user = mock_user
    mock_connection.path_params = {"team_id": team_id}
    mock_handler = Mock()

    with pytest.raises(PermissionDeniedException) as exc_info:
        requires_team_membership(mock_connection, mock_handler)

    assert "Insufficient permissions" in str(exc_info.value.detail)


def test_non_superuser_role_fails() -> None:
    """Test that user with non-superuser role fails."""
    team_id = uuid4()

    mock_role = Mock()
    mock_role.role_name = "regular_user"

    mock_user = Mock()
    mock_user.is_superuser = False
    mock_user.roles = [mock_role]
    mock_user.teams = []

    mock_connection = Mock()
    mock_connection.user = mock_user
    mock_connection.path_params = {"team_id": team_id}
    mock_handler = Mock()

    with pytest.raises(PermissionDeniedException):
        requires_team_membership(mock_connection, mock_handler)


def test_admin_superuser_flag_passes() -> None:
    """Test that is_superuser=True passes the guard."""
    team_id = uuid4()

    mock_user = Mock()
    mock_user.is_superuser = True
    mock_user.roles = []
    mock_user.teams = []

    mock_connection = Mock()
    mock_connection.user = mock_user
    mock_connection.path_params = {"team_id": team_id}
    mock_handler = Mock()

    # Should not raise
    requires_team_admin(mock_connection, mock_handler)


def test_admin_superuser_role_passes() -> None:
    """Test that user with SUPERUSER_ACCESS_ROLE passes."""
    team_id = uuid4()

    mock_role = Mock()
    mock_role.role_name = constants.SUPERUSER_ACCESS_ROLE

    mock_user = Mock()
    mock_user.is_superuser = False
    mock_user.roles = [mock_role]
    mock_user.teams = []

    mock_connection = Mock()
    mock_connection.user = mock_user
    mock_connection.path_params = {"team_id": team_id}
    mock_handler = Mock()

    # Should not raise
    requires_team_admin(mock_connection, mock_handler)


def test_team_admin_passes() -> None:
    """Test that team admin passes the guard."""
    team_id = uuid4()

    mock_team = Mock()
    mock_team.id = team_id

    mock_membership = Mock()
    mock_membership.team = mock_team
    mock_membership.role = m.TeamRoles.ADMIN

    mock_user = Mock()
    mock_user.is_superuser = False
    mock_user.roles = []
    mock_user.teams = [mock_membership]

    mock_connection = Mock()
    mock_connection.user = mock_user
    mock_connection.path_params = {"team_id": team_id}
    mock_handler = Mock()

    # Should not raise
    requires_team_admin(mock_connection, mock_handler)


def test_team_member_fails() -> None:
    """Test that regular team member fails admin guard."""
    team_id = uuid4()

    mock_team = Mock()
    mock_team.id = team_id

    mock_membership = Mock()
    mock_membership.team = mock_team
    mock_membership.role = m.TeamRoles.MEMBER  # Not admin

    mock_user = Mock()
    mock_user.is_superuser = False
    mock_user.roles = []
    mock_user.teams = [mock_membership]

    mock_connection = Mock()
    mock_connection.user = mock_user
    mock_connection.path_params = {"team_id": team_id}
    mock_handler = Mock()

    with pytest.raises(PermissionDeniedException) as exc_info:
        requires_team_admin(mock_connection, mock_handler)

    assert "Insufficient permissions" in str(exc_info.value.detail)


def test_admin_of_different_team_fails() -> None:
    """Test that admin of different team fails."""
    team_id = uuid4()
    other_team_id = uuid4()

    mock_team = Mock()
    mock_team.id = other_team_id  # Different team

    mock_membership = Mock()
    mock_membership.team = mock_team
    mock_membership.role = m.TeamRoles.ADMIN

    mock_user = Mock()
    mock_user.is_superuser = False
    mock_user.roles = []
    mock_user.teams = [mock_membership]

    mock_connection = Mock()
    mock_connection.user = mock_user
    mock_connection.path_params = {"team_id": team_id}
    mock_handler = Mock()

    with pytest.raises(PermissionDeniedException):
        requires_team_admin(mock_connection, mock_handler)


def test_ownership_superuser_flag_passes() -> None:
    """Test that is_superuser=True passes the guard."""
    team_id = uuid4()

    mock_user = Mock()
    mock_user.is_superuser = True
    mock_user.roles = []
    mock_user.teams = []

    mock_connection = Mock()
    mock_connection.user = mock_user
    mock_connection.path_params = {"team_id": team_id}
    mock_handler = Mock()

    # Should not raise
    requires_team_ownership(mock_connection, mock_handler)


def test_ownership_superuser_role_passes() -> None:
    """Test that user with SUPERUSER_ACCESS_ROLE passes."""
    team_id = uuid4()

    mock_role = Mock()
    mock_role.role_name = constants.SUPERUSER_ACCESS_ROLE

    mock_user = Mock()
    mock_user.is_superuser = False
    mock_user.roles = [mock_role]
    mock_user.teams = []

    mock_connection = Mock()
    mock_connection.user = mock_user
    mock_connection.path_params = {"team_id": team_id}
    mock_handler = Mock()

    # Should not raise
    requires_team_ownership(mock_connection, mock_handler)


def test_team_owner_passes() -> None:
    """Test that team owner passes the guard."""
    team_id = uuid4()

    mock_team = Mock()
    mock_team.id = team_id

    mock_membership = Mock()
    mock_membership.team = mock_team
    mock_membership.is_owner = True

    mock_user = Mock()
    mock_user.is_superuser = False
    mock_user.roles = []
    mock_user.teams = [mock_membership]

    mock_connection = Mock()
    mock_connection.user = mock_user
    mock_connection.path_params = {"team_id": team_id}
    mock_handler = Mock()

    # Should not raise
    requires_team_ownership(mock_connection, mock_handler)


def test_team_admin_non_owner_fails() -> None:
    """Test that team admin who is not owner fails."""
    team_id = uuid4()

    mock_team = Mock()
    mock_team.id = team_id

    mock_membership = Mock()
    mock_membership.team = mock_team
    mock_membership.is_owner = False  # Not owner

    mock_user = Mock()
    mock_user.is_superuser = False
    mock_user.roles = []
    mock_user.teams = [mock_membership]

    mock_connection = Mock()
    mock_connection.user = mock_user
    mock_connection.path_params = {"team_id": team_id}
    mock_handler = Mock()

    with pytest.raises(PermissionDeniedException) as exc_info:
        requires_team_ownership(mock_connection, mock_handler)

    assert "Insufficient permissions" in str(exc_info.value.detail)


def test_owner_of_different_team_fails() -> None:
    """Test that owner of different team fails."""
    team_id = uuid4()
    other_team_id = uuid4()

    mock_team = Mock()
    mock_team.id = other_team_id  # Different team

    mock_membership = Mock()
    mock_membership.team = mock_team
    mock_membership.is_owner = True

    mock_user = Mock()
    mock_user.is_superuser = False
    mock_user.roles = []
    mock_user.teams = [mock_membership]

    mock_connection = Mock()
    mock_connection.user = mock_user
    mock_connection.path_params = {"team_id": team_id}
    mock_handler = Mock()

    with pytest.raises(PermissionDeniedException):
        requires_team_ownership(mock_connection, mock_handler)


def test_no_memberships_fails() -> None:
    """Test that user with no memberships fails."""
    team_id = uuid4()

    mock_user = Mock()
    mock_user.is_superuser = False
    mock_user.roles = []
    mock_user.teams = []

    mock_connection = Mock()
    mock_connection.user = mock_user
    mock_connection.path_params = {"team_id": team_id}
    mock_handler = Mock()

    with pytest.raises(PermissionDeniedException):
        requires_team_ownership(mock_connection, mock_handler)


def test_owner_passes_all_guards() -> None:
    """Test that team owner passes all guards."""
    team_id = uuid4()

    mock_team = Mock()
    mock_team.id = team_id

    mock_membership = Mock()
    mock_membership.team = mock_team
    mock_membership.role = m.TeamRoles.ADMIN
    mock_membership.is_owner = True

    mock_user = Mock()
    mock_user.is_superuser = False
    mock_user.roles = []
    mock_user.teams = [mock_membership]

    mock_connection = Mock()
    mock_connection.user = mock_user
    mock_connection.path_params = {"team_id": team_id}
    mock_handler = Mock()

    # All guards should pass
    requires_team_membership(mock_connection, mock_handler)
    requires_team_admin(mock_connection, mock_handler)
    requires_team_ownership(mock_connection, mock_handler)


def test_admin_passes_membership_and_admin() -> None:
    """Test that admin passes membership and admin guards but not ownership."""
    team_id = uuid4()

    mock_team = Mock()
    mock_team.id = team_id

    mock_membership = Mock()
    mock_membership.team = mock_team
    mock_membership.role = m.TeamRoles.ADMIN
    mock_membership.is_owner = False

    mock_user = Mock()
    mock_user.is_superuser = False
    mock_user.roles = []
    mock_user.teams = [mock_membership]

    mock_connection = Mock()
    mock_connection.user = mock_user
    mock_connection.path_params = {"team_id": team_id}
    mock_handler = Mock()

    # Should pass membership and admin
    requires_team_membership(mock_connection, mock_handler)
    requires_team_admin(mock_connection, mock_handler)

    # Should fail ownership
    with pytest.raises(PermissionDeniedException):
        requires_team_ownership(mock_connection, mock_handler)


def test_member_passes_only_membership() -> None:
    """Test that regular member only passes membership guard."""
    team_id = uuid4()

    mock_team = Mock()
    mock_team.id = team_id

    mock_membership = Mock()
    mock_membership.team = mock_team
    mock_membership.role = m.TeamRoles.MEMBER
    mock_membership.is_owner = False

    mock_user = Mock()
    mock_user.is_superuser = False
    mock_user.roles = []
    mock_user.teams = [mock_membership]

    mock_connection = Mock()
    mock_connection.user = mock_user
    mock_connection.path_params = {"team_id": team_id}
    mock_handler = Mock()

    # Should pass membership
    requires_team_membership(mock_connection, mock_handler)

    # Should fail admin and ownership
    with pytest.raises(PermissionDeniedException):
        requires_team_admin(mock_connection, mock_handler)

    with pytest.raises(PermissionDeniedException):
        requires_team_ownership(mock_connection, mock_handler)


def test_member_of_requested_team_among_many() -> None:
    """Test user who is member of requested team among multiple teams."""
    team_id = uuid4()
    other_team_id = uuid4()

    mock_team1 = Mock()
    mock_team1.id = other_team_id

    mock_team2 = Mock()
    mock_team2.id = team_id

    mock_membership1 = Mock()
    mock_membership1.team = mock_team1

    mock_membership2 = Mock()
    mock_membership2.team = mock_team2

    mock_user = Mock()
    mock_user.is_superuser = False
    mock_user.roles = []
    mock_user.teams = [mock_membership1, mock_membership2]

    mock_connection = Mock()
    mock_connection.user = mock_user
    mock_connection.path_params = {"team_id": team_id}
    mock_handler = Mock()

    # Should pass
    requires_team_membership(mock_connection, mock_handler)


def test_admin_in_one_member_in_another() -> None:
    """Test user who is admin in one team but member in another."""
    admin_team_id = uuid4()
    member_team_id = uuid4()

    mock_admin_team = Mock()
    mock_admin_team.id = admin_team_id

    mock_member_team = Mock()
    mock_member_team.id = member_team_id

    mock_admin_membership = Mock()
    mock_admin_membership.team = mock_admin_team
    mock_admin_membership.role = m.TeamRoles.ADMIN
    mock_admin_membership.is_owner = False

    mock_member_membership = Mock()
    mock_member_membership.team = mock_member_team
    mock_member_membership.role = m.TeamRoles.MEMBER
    mock_member_membership.is_owner = False

    mock_user = Mock()
    mock_user.is_superuser = False
    mock_user.roles = []
    mock_user.teams = [mock_admin_membership, mock_member_membership]

    mock_handler = Mock()

    # Should pass admin for admin_team
    mock_connection = Mock()
    mock_connection.user = mock_user
    mock_connection.path_params = {"team_id": admin_team_id}
    requires_team_admin(mock_connection, mock_handler)

    # Should fail admin for member_team
    mock_connection2 = Mock()
    mock_connection2.user = mock_user
    mock_connection2.path_params = {"team_id": member_team_id}
    with pytest.raises(PermissionDeniedException):
        requires_team_admin(mock_connection2, mock_handler)

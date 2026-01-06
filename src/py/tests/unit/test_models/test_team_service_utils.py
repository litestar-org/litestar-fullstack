"""Unit tests for TeamService utility methods.

These tests verify static/class methods that don't require database interaction.
"""

from __future__ import annotations

import pytest

from app.domain.teams.services import TeamService
from app.lib import constants
from tests.factories import RoleFactory, UserFactory, UserRoleFactory

pytestmark = [pytest.mark.unit, pytest.mark.services]


def test_can_view_all_superuser_flag() -> None:
    """Test can_view_all with superuser flag."""
    user = UserFactory.build(is_superuser=True)
    user.roles = []

    result = TeamService.can_view_all(user)
    assert result is True


def test_can_view_all_superuser_role() -> None:
    """Test can_view_all with superuser role."""
    user = UserFactory.build(is_superuser=False)

    # Create role with superuser access using factory
    role = RoleFactory.build(name=constants.SUPERUSER_ACCESS_ROLE)
    user_role = UserRoleFactory.build(user_id=user.id, role_id=role.id)
    user_role.role = role
    user.roles = [user_role]

    result = TeamService.can_view_all(user)
    assert result is True


def test_can_view_all_regular_user() -> None:
    """Test can_view_all with regular user."""
    user = UserFactory.build(is_superuser=False)

    # Create role without superuser access using factory
    role = RoleFactory.build(name="regular_user")
    user_role = UserRoleFactory.build(user_id=user.id, role_id=role.id)
    user_role.role = role
    user.roles = [user_role]

    result = TeamService.can_view_all(user)
    assert result is False


def test_can_view_all_user_no_roles() -> None:
    """Test can_view_all with user having no roles."""
    user = UserFactory.build(is_superuser=False)
    user.roles = []

    result = TeamService.can_view_all(user)
    assert result is False

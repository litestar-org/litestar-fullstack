"""Comprehensive tests for TeamService."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast
from uuid import uuid4

import pytest
from advanced_alchemy.exceptions import RepositoryError
from sqlalchemy.exc import IntegrityError

from app.db import models as m
from app.domain.teams.services import TeamService
from app.lib import constants
from tests.factories import RoleFactory, TagFactory, TeamFactory, TeamMemberFactory, UserFactory, UserRoleFactory

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = [pytest.mark.unit, pytest.mark.services]


@pytest.mark.anyio
async def test_create_team_basic(session: AsyncSession, team_service: TeamService) -> None:
    """Test basic team creation."""
    team_data = {"name": "Test Team", "description": "A test team"}

    team = await team_service.create(data=team_data)

    assert team.name == "Test Team"
    assert team.description == "A test team"
    assert team.slug is not None
    assert team.is_active is True
    assert team.id is not None


@pytest.mark.anyio
async def test_create_team_with_owner(session: AsyncSession, team_service: TeamService) -> None:
    """Test team creation with owner."""
    # Create owner user
    owner = UserFactory.build()
    session.add(owner)
    await session.commit()
    await session.refresh(owner)

    team_data = {"name": "Owner Team", "description": "Team with owner", "owner_id": owner.id}

    team = await team_service.create(data=team_data)

    assert team.name == "Owner Team"
    assert len(team.members) == 1

    owner_member = team.members[0]
    assert owner_member.user_id == owner.id
    assert owner_member.role == m.TeamRoles.ADMIN
    assert owner_member.is_owner is True


@pytest.mark.anyio
async def test_create_team_with_tags(session: AsyncSession, team_service: TeamService) -> None:
    """Test team creation with tags."""
    team_data = {"name": "Tagged Team", "description": "Team with tags", "tags": ["development", "backend", "api"]}

    team = await team_service.create(data=team_data)

    assert team.name == "Tagged Team"
    assert len(team.tags) == 3

    tag_names = [tag.name for tag in team.tags]
    assert "development" in tag_names
    assert "backend" in tag_names
    assert "api" in tag_names


@pytest.mark.anyio
async def test_create_team_slug_generation(session: AsyncSession, team_service: TeamService) -> None:
    """Test automatic slug generation."""
    team_data = {"name": "Team With Spaces And CAPS", "description": "Testing slug generation"}

    team = await team_service.create(data=team_data)

    assert team.slug is not None
    assert " " not in team.slug
    assert team.slug.islower()


@pytest.mark.anyio
async def test_create_team_duplicate_name_different_slugs(
    self, session: AsyncSession, team_service: TeamService
) -> None:
    """Test that duplicate team names get different slugs."""
    team_data1 = {"name": "Test Team", "description": "First team"}
    team_data2 = {"name": "Test Team", "description": "Second team"}

    team1 = await team_service.create(data=team_data1)
    team2 = await team_service.create(data=team_data2)

    assert team1.name == team2.name
    assert team1.slug != team2.slug
    assert team1.id != team2.id


@pytest.mark.anyio
async def test_get_team_by_id(session: AsyncSession, team_service: TeamService) -> None:
    """Test getting team by ID."""
    team = TeamFactory.build()
    session.add(team)
    await session.commit()

    found_team = await team_service.get_one(item_id=team.id)

    assert found_team.id == team.id
    assert found_team.name == team.name


@pytest.mark.anyio
async def test_get_team_by_slug(session: AsyncSession, team_service: TeamService) -> None:
    """Test getting team by slug."""
    team = TeamFactory.build(slug="test-team-slug")
    session.add(team)
    await session.commit()

    found_team = await team_service.get_one(slug="test-team-slug")

    assert found_team.id == team.id
    assert found_team.slug == "test-team-slug"


@pytest.mark.anyio
async def test_update_team(session: AsyncSession, team_service: TeamService) -> None:
    """Test updating team information."""
    team = TeamFactory.build(name="Original Name")
    session.add(team)
    await session.commit()

    update_data = {"name": "Updated Name", "description": "Updated description"}

    updated_team = await team_service.update(item_id=team.id, data=update_data)

    assert updated_team.name == "Updated Name"
    assert updated_team.description == "Updated description"
    assert updated_team.id == team.id


@pytest.mark.anyio
async def test_update_team_with_new_tags(session: AsyncSession, team_service: TeamService) -> None:
    """Test updating team with new tags."""
    # Create team with initial tags
    team_data = {"name": "Team to Update", "tags": ["tag1", "tag2"]}
    team = await team_service.create(data=team_data)

    # Update with new tags
    update_data = {
        "tags": ["tag2", "tag3", "tag4"]  # Remove tag1, keep tag2, add tag3 and tag4
    }

    updated_team = await team_service.update(item_id=team.id, data=update_data)

    tag_names = [tag.name for tag in updated_team.tags]
    assert "tag1" not in tag_names  # Removed
    assert "tag2" in tag_names  # Kept
    assert "tag3" in tag_names  # Added
    assert "tag4" in tag_names  # Added
    assert len(updated_team.tags) == 3


@pytest.mark.anyio
async def test_delete_team(session: AsyncSession, team_service: TeamService) -> None:
    """Test deleting team."""
    team = TeamFactory.build()
    session.add(team)
    await session.commit()

    await team_service.delete(item_id=team.id)

    # Verify team is deleted
    deleted_team = await team_service.get_one_or_none(item_id=team.id)
    assert deleted_team is None


@pytest.mark.anyio
async def test_list_teams(session: AsyncSession, team_service: TeamService) -> None:
    """Test listing teams."""
    teams = [TeamFactory.build() for _ in range(3)]
    session.add_all(teams)
    await session.commit()

    result = await team_service.list()

    assert len(result) >= 3  # At least the 3 we created


@pytest.mark.anyio
async def test_create_team_with_owner_user_object(session: AsyncSession, team_service: TeamService) -> None:
    """Test team creation with owner as User object."""
    owner = UserFactory.build()
    session.add(owner)
    await session.commit()
    await session.refresh(owner)

    team_data = {"name": "Owner Team", "owner": owner}

    team = await team_service.create(data=team_data)

    assert len(team.members) == 1
    owner_member = team.members[0]
    assert owner_member.user_id == owner.id
    assert owner_member.is_owner is True
    assert owner_member.role == m.TeamRoles.ADMIN


@pytest.mark.anyio
async def test_update_team_change_owner(session: AsyncSession, team_service: TeamService) -> None:
    """Test changing team owner."""
    # Create team with initial owner
    original_owner = UserFactory.build()
    new_owner = UserFactory.build()
    session.add_all([original_owner, new_owner])
    await session.commit()

    team_data = {"name": "Ownership Test Team", "owner_id": original_owner.id}
    team = await team_service.create(data=team_data)

    # Add new owner as member first
    new_member = TeamMemberFactory.build(team_id=team.id, user_id=new_owner.id, role=m.TeamRoles.MEMBER, is_owner=False)
    session.add(new_member)
    await session.commit()

    # Update team with new owner
    update_data = {"owner_id": new_owner.id}
    updated_team = await team_service.update(item_id=team.id, data=update_data)

    # Check that new owner has correct role and ownership
    new_owner_member = next((m for m in updated_team.members if m.user_id == new_owner.id), None)
    assert new_owner_member is not None
    assert new_owner_member.is_owner is True
    assert new_owner_member.role == m.TeamRoles.ADMIN


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


@pytest.mark.anyio
async def test_populate_slug_when_missing(session: AsyncSession, team_service: TeamService) -> None:
    """Test slug population when not provided."""
    team_data = {"name": "Team Without Slug"}

    # Call the private method directly for testing
    result = await team_service._populate_slug(team_data)

    assert isinstance(result, dict)
    assert "slug" in result
    assert result["slug"] is not None


@pytest.mark.anyio
async def test_populate_slug_when_provided(session: AsyncSession, team_service: TeamService) -> None:
    """Test slug is preserved when provided."""
    team_data = {"name": "Team With Slug", "slug": "custom-slug"}

    result = await team_service._populate_slug(team_data)

    assert isinstance(result, dict)
    assert result["slug"] == "custom-slug"


@pytest.mark.anyio
async def test_populate_slug_without_name(session: AsyncSession, team_service: TeamService) -> None:
    """Test slug population when name is missing."""
    team_data = {"description": "Team without name"}

    result = await team_service._populate_slug(team_data)

    # Should not add slug when name is missing
    assert isinstance(result, dict)
    assert "slug" not in result


@pytest.mark.anyio
async def test_populate_with_new_tags(session: AsyncSession, team_service: TeamService) -> None:
    """Test adding new tags to team."""
    team_data = {"id": uuid4(), "name": "Tag Test Team", "tags": ["new-tag-1", "new-tag-2"]}

    # Convert to model to test tag population
    result = await team_service._populate_with_owner_and_tags(team_data, "create")
    team_obj = cast("m.Team", result)

    assert hasattr(team_obj, "tags")
    assert len(team_obj.tags) == 2


@pytest.mark.anyio
async def test_populate_with_existing_tags(session: AsyncSession, team_service: TeamService) -> None:
    """Test handling existing tags."""
    # Create existing tags
    existing_tag = TagFactory.build(name="existing-tag")
    session.add(existing_tag)
    await session.commit()

    team_data = {"id": uuid4(), "name": "Existing Tag Team", "tags": ["existing-tag", "new-tag"]}

    result = await team_service._populate_with_owner_and_tags(team_data, "create")
    team_obj = cast("m.Team", result)

    assert hasattr(team_obj, "tags")
    tag_names = [tag.name for tag in team_obj.tags]
    assert "existing-tag" in tag_names
    assert "new-tag" in tag_names


@pytest.mark.anyio
async def test_remove_tags_from_team(session: AsyncSession, team_service: TeamService) -> None:
    """Test removing tags from existing team."""
    # Create team with initial tags
    team_data = {"name": "Tag Removal Test", "tags": ["tag1", "tag2", "tag3"]}
    team = await team_service.create(data=team_data)

    # Update to remove some tags
    update_data = {
        "tags": ["tag1", "tag3"]  # Remove tag2
    }

    updated_team = await team_service.update(item_id=team.id, data=update_data)

    tag_names = [tag.name for tag in updated_team.tags]
    assert "tag1" in tag_names
    assert "tag2" not in tag_names  # Should be removed
    assert "tag3" in tag_names
    assert len(updated_team.tags) == 2


@pytest.mark.anyio
async def test_get_nonexistent_team(team_service: TeamService) -> None:
    """Test getting non-existent team returns None."""
    result = await team_service.get_one_or_none(item_id=uuid4())
    assert result is None


@pytest.mark.anyio
async def test_update_nonexistent_team(team_service: TeamService) -> None:
    """Test updating non-existent team raises error."""
    with pytest.raises(RepositoryError):
        await team_service.update(item_id=uuid4(), data={"name": "Updated"})


@pytest.mark.anyio
async def test_delete_nonexistent_team(team_service: TeamService) -> None:
    """Test deleting non-existent team raises error."""
    with pytest.raises(RepositoryError):
        await team_service.delete(item_id=uuid4())


@pytest.mark.anyio
async def test_create_team_empty_name(team_service: TeamService) -> None:
    """Test creating team with empty name."""
    team_data = {"name": "", "description": "Empty name test"}

    # This should either raise an error or handle gracefully
    # Depending on validation rules
    try:
        team = await team_service.create(data=team_data)
    except (RepositoryError, IntegrityError, ValueError):
        return
    assert team.name == ""


@pytest.mark.anyio
async def test_create_team_with_nonexistent_owner(session: AsyncSession, team_service: TeamService) -> None:
    """Test creating team with non-existent owner ID."""
    team_data = {
        "name": "Invalid Owner Team",
        "owner_id": uuid4(),  # Non-existent user ID
    }

    # Should handle gracefully - either create without owner or raise error
    try:
        team = await team_service.create(data=team_data)
    except (RepositoryError, IntegrityError, ValueError):
        return
    assert len(team.members) == 0


@pytest.mark.anyio
async def test_full_team_lifecycle(session: AsyncSession, team_service: TeamService) -> None:
    """Test complete team lifecycle: create, update, add members, delete."""
    # Create owner
    owner = UserFactory.build()
    session.add(owner)
    await session.commit()

    # Create team
    team_data = {
        "name": "Lifecycle Test Team",
        "description": "Testing full lifecycle",
        "owner_id": owner.id,
        "tags": ["lifecycle", "test"],
    }
    team = await team_service.create(data=team_data)

    # Verify creation
    assert team.name == "Lifecycle Test Team"
    assert len(team.members) == 1
    assert team.members[0].is_owner is True
    assert len(team.tags) == 2

    # Update team
    update_data = {
        "description": "Updated description",
        "tags": ["lifecycle", "updated"],  # Change tags
    }
    updated_team = await team_service.update(item_id=team.id, data=update_data)

    # Verify update
    assert updated_team.description == "Updated description"
    tag_names = [tag.name for tag in updated_team.tags]
    assert "updated" in tag_names
    assert "test" not in tag_names

    # Delete team
    await team_service.delete(item_id=team.id)

    # Verify deletion
    deleted_team = await team_service.get_one_or_none(item_id=team.id)
    assert deleted_team is None


@pytest.mark.anyio
async def test_team_with_multiple_members_and_tags(session: AsyncSession, team_service: TeamService) -> None:
    """Test team with complex member and tag relationships."""
    # Create users
    owner = UserFactory.build()
    member1 = UserFactory.build()
    member2 = UserFactory.build()
    session.add_all([owner, member1, member2])
    await session.commit()

    # Create team with owner
    team_data = {
        "name": "Complex Team",
        "description": "Team with multiple relationships",
        "owner_id": owner.id,
        "tags": ["complex", "relationships", "testing"],
    }
    team = await team_service.create(data=team_data)

    # Add additional members manually (simulating team invitation acceptance)
    member1_membership = TeamMemberFactory.build(team_id=team.id, user_id=member1.id, role=m.TeamRoles.MEMBER)
    member2_membership = TeamMemberFactory.build(team_id=team.id, user_id=member2.id, role=m.TeamRoles.MEMBER)
    session.add_all([member1_membership, member2_membership])
    await session.commit()

    # Refresh team to get updated members
    await session.refresh(team)

    # Verify complex relationships
    assert len(team.members) == 3  # Owner + 2 members
    assert len(team.tags) == 3

    # Verify owner has correct permissions
    owner_member = next((m for m in team.members if m.user_id == owner.id), None)
    assert owner_member is not None
    assert owner_member.is_owner is True
    assert owner_member.role == m.TeamRoles.ADMIN

    # Verify regular members
    regular_members = [m for m in team.members if not m.is_owner]
    assert len(regular_members) == 2
    for member in regular_members:
        assert member.role == m.TeamRoles.MEMBER
        assert member.is_owner is False

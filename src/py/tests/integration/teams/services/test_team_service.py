"""Integration tests for ``TeamService`` persistence, slug generation, ownership, and tag syncing."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

import pytest
from advanced_alchemy.exceptions import RepositoryError

from app.db import models as m
from tests.factories import TagFactory, TeamFactory, TeamMemberFactory, UserFactory

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.domain.teams.services import TeamService

pytestmark = [pytest.mark.anyio, pytest.mark.integration, pytest.mark.services]


async def test_create_team_with_owner_and_tags(session: AsyncSession, team_service: TeamService) -> None:
    """Creating a team assigns the owner as ADMIN, generates a lowercase slug, and attaches tags."""
    owner = UserFactory.build()
    session.add(owner)
    await session.commit()

    team = await team_service.create(
        data={
            "name": "Tagged Platform Team",
            "description": "Team with owner and tags",
            "tags": ["development", "backend", "api"],
            "owner_id": owner.id,
        },
        auto_refresh=True,
    )
    await session.refresh(team, ["members", "tags"])

    assert team.name == "Tagged Platform Team"
    assert team.slug is not None
    assert " " not in team.slug
    assert team.slug.islower()
    assert team.is_active is True
    assert len(team.members) == 1
    assert team.members[0].user_id == owner.id
    assert team.members[0].is_owner is True
    assert team.members[0].role == m.TeamRoles.ADMIN
    assert {tag.name for tag in team.tags} == {"development", "backend", "api"}


async def test_create_team_duplicate_name_gets_unique_slugs(session: AsyncSession, team_service: TeamService) -> None:
    """Duplicate team names receive distinct generated slugs."""
    owner = UserFactory.build()
    session.add(owner)
    await session.commit()

    team1 = await team_service.create(data={"name": "Shared Name", "description": "First", "owner_id": owner.id})
    team2 = await team_service.create(data={"name": "Shared Name", "description": "Second", "owner_id": owner.id})

    assert team1.name == team2.name
    assert team1.slug != team2.slug
    assert team1.id != team2.id


async def test_update_team_tags_reuses_existing_and_removes_stale(
    session: AsyncSession,
    team_service: TeamService,
) -> None:
    """Updating team tags attaches existing/new tags and detaches removed tags."""
    owner = UserFactory.build()
    existing_tag = TagFactory.build(name="existing-tag")
    session.add_all([owner, existing_tag])
    await session.commit()

    team = await team_service.create(
        data={"name": "Tag Sync Team", "tags": ["existing-tag", "old-tag"], "owner_id": owner.id},
        auto_refresh=True,
    )
    updated = await team_service.update(
        item_id=team.id,
        data={"description": "Updated", "tags": ["existing-tag", "new-tag"]},
        auto_refresh=True,
    )
    await session.refresh(updated, ["tags"])

    assert updated.description == "Updated"
    assert {tag.name for tag in updated.tags} == {"existing-tag", "new-tag"}


async def test_update_team_transfers_owner_role(session: AsyncSession, team_service: TeamService) -> None:
    """Updating ``owner_id`` promotes the target member to ADMIN owner."""
    original_owner = UserFactory.build()
    new_owner = UserFactory.build()
    session.add_all([original_owner, new_owner])
    await session.commit()

    team = await team_service.create(data={"name": "Ownership Team", "owner_id": original_owner.id})
    session.add(TeamMemberFactory.build(team_id=team.id, user_id=new_owner.id, role=m.TeamRoles.MEMBER, is_owner=False))
    await session.commit()

    updated = await team_service.update(item_id=team.id, data={"owner_id": new_owner.id})
    promoted = next((member for member in updated.members if member.user_id == new_owner.id), None)
    assert promoted is not None
    assert promoted.is_owner is True
    assert promoted.role == m.TeamRoles.ADMIN


async def test_get_list_delete_and_not_found_errors(session: AsyncSession, team_service: TeamService) -> None:
    """Standard read, list, delete, and missing-ID error paths work cleanly."""
    team = TeamFactory.build(slug="lookup-team-slug")
    session.add(team)
    await session.commit()

    by_id = await team_service.get_one(id=team.id)
    by_slug = await team_service.get_one(slug="lookup-team-slug")
    assert by_id.id == by_slug.id == team.id
    assert len(await team_service.list()) >= 1

    await team_service.delete(item_id=team.id)
    assert await team_service.get_one_or_none(id=team.id) is None

    with pytest.raises(RepositoryError):
        await team_service.update(item_id=uuid4(), data={"name": "Missing"})

    with pytest.raises(RepositoryError):
        await team_service.delete(item_id=uuid4())


async def test_pending_invitations_exclude_accepted_ones(session: AsyncSession, team_service: TeamService) -> None:
    """``Team.pending_invitations`` loads only unaccepted invitations, filtered with an ``IS false`` predicate."""
    owner = UserFactory.build()
    session.add(owner)
    await session.commit()
    team = await team_service.create(data={"name": "Invitation Team", "owner_id": owner.id})
    session.add_all(
        [
            m.TeamInvitation(
                team_id=team.id,
                email=email,
                is_accepted=is_accepted,
                invited_by_id=owner.id,
                invited_by_email=owner.email,
            )
            for email, is_accepted in (("pending@example.com", False), ("accepted@example.com", True))
        ]
    )
    await session.commit()

    await session.refresh(team, ["pending_invitations"])

    assert [invitation.email for invitation in team.pending_invitations] == ["pending@example.com"]
    assert "is_accepted IS false" in str(m.Team.pending_invitations.property.primaryjoin)

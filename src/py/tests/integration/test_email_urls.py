"""Integration tests for email URL generation."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest
from litestar_email import InMemoryBackend

from app.db import models as m

if TYPE_CHECKING:
    from collections.abc import Callable, Coroutine

    from litestar.testing import AsyncTestClient

pytestmark = [pytest.mark.anyio, pytest.mark.integration, pytest.mark.teams, pytest.mark.email]


@pytest.fixture(autouse=True)
def clear_email_outbox() -> None:
    """Clear email outbox before each test."""
    InMemoryBackend.clear()


async def test_team_invitation_email_url(
    authenticated_client: AsyncTestClient,
    test_team: m.Team,
    await_events: Callable[[], Coroutine[Any, Any, None]],
) -> None:
    """Test that team invitation email contains the correct URL, not example.com."""
    invitation_data = {
        "email": "newmember@example.com",
        "role": m.TeamRoles.MEMBER.value,
    }

    # This triggers the 'team_invitation_created' event
    response = await authenticated_client.post(
        f"/api/teams/{test_team.id}/invitations",
        json=invitation_data,
    )
    assert response.status_code == 201

    # Wait for background tasks/events to complete
    await await_events()

    # Verify outbox
    assert len(InMemoryBackend.outbox) == 1
    from litestar_email import EmailMultiAlternatives

    message = InMemoryBackend.outbox[0]
    assert isinstance(message, EmailMultiAlternatives)

    # Check that it contains the expected path segments
    assert message.html_body is not None
    assert "/teams/" in message.html_body
    assert "/invitations/" in message.html_body

    # This should FAIL currently because it's hardcoded to https://example.com in listeners.py
    assert "example.com" not in message.html_body

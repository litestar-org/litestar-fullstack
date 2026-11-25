"""Integration tests for user administration, role assignment, and self-service profile routes."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from app.db import models as m
from tests.integration.conftest import fetch_csrf_headers, login_session_client, reset_client_session

if TYPE_CHECKING:
    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = [pytest.mark.anyio, pytest.mark.integration, pytest.mark.auth, pytest.mark.endpoints]

SUPERUSER_ID = "97108ac1-ffcb-411d-8b1e-d9183399f63b"
REGULAR_USER_ID = "5ef29f3c-3560-4d15-ba6b-a2e5c721e4d2"
USER_TEAM_ID = "97108ac1-ffcb-411d-8b1e-d9183399f63b"
OTHER_TEAM_ID = "81108ac1-ffcb-411d-8b1e-d91833999999"


async def test_user_routes_require_authentication(seeded_client: AsyncClient) -> None:
    """Unauthenticated requests to ``/api/users`` and ``/api/admin/users`` return 401."""
    csrf = await fetch_csrf_headers(seeded_client)
    assert (await seeded_client.get("/api/users")).status_code == 401
    assert (await seeded_client.get(f"/api/users/{SUPERUSER_ID}")).status_code == 401
    assert (
        await seeded_client.post(
            "/api/users",
            json={"name": "New User", "email": "new-user@example.com", "password": "Test_Password1!"},
            headers=csrf,
        )
    ).status_code == 401
    assert (
        await seeded_client.patch(
            f"/api/users/{SUPERUSER_ID}",
            json={"name": "Unauthorized Update"},
            headers=csrf,
        )
    ).status_code == 401
    assert (await seeded_client.delete(f"/api/users/{SUPERUSER_ID}", headers=csrf)).status_code == 401
    assert (await seeded_client.get("/api/admin/users/")).status_code == 401


async def test_regular_user_forbidden_from_admin_user_routes(seeded_client: AsyncClient) -> None:
    """Non-superuser accounts receive 403 on ``/api/users`` and ``/api/admin/users``."""
    csrf = await login_session_client(seeded_client, "user@example.com", "Test_Password2!")
    assert (await seeded_client.get("/api/users")).status_code == 403
    assert (await seeded_client.get(f"/api/users/{SUPERUSER_ID}")).status_code == 403
    assert (
        await seeded_client.post(
            "/api/users",
            json={"name": "Blocked User", "email": "blocked@example.com", "password": "Test_Password1!"},
            headers=csrf,
        )
    ).status_code == 403
    assert (
        await seeded_client.patch(
            f"/api/users/{SUPERUSER_ID}",
            json={"name": "Blocked Update"},
            headers=csrf,
        )
    ).status_code == 403
    assert (await seeded_client.delete(f"/api/users/{SUPERUSER_ID}", headers=csrf)).status_code == 403
    assert (await seeded_client.get("/api/admin/users/")).status_code == 403


async def test_superuser_user_crud_and_admin_endpoints(superuser_client: AsyncClient) -> None:
    """Superusers can list, retrieve, create, update, and delete users without cascading owned teams."""
    list_resp = await superuser_client.get("/api/users")
    assert list_resp.status_code == 200
    assert int(list_resp.json()["total"]) > 0

    get_resp = await superuser_client.get(f"/api/users/{SUPERUSER_ID}")
    assert get_resp.status_code == 200
    assert get_resp.json()["email"] == "superuser@example.com"

    create_resp = await superuser_client.post(
        "/api/users",
        json={"name": "Created User", "email": "created-user@example.com", "password": "Test_Password1!"},
    )
    assert create_resp.status_code == 201

    update_resp = await superuser_client.patch(
        f"/api/users/{REGULAR_USER_ID}",
        json={"name": "Name Changed"},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["name"] == "Name Changed"

    admin_list = await superuser_client.get("/api/admin/users/")
    assert admin_list.status_code == 200
    assert admin_list.json()["total"] >= 2

    admin_detail = await superuser_client.get(f"/api/admin/users/{REGULAR_USER_ID}")
    assert admin_detail.status_code == 200
    assert admin_detail.json()["email"] == "user@example.com"

    self_delete = await superuser_client.delete(f"/api/admin/users/{SUPERUSER_ID}")
    assert self_delete.status_code == 403

    delete_resp = await superuser_client.delete(f"/api/users/{REGULAR_USER_ID}")
    assert delete_resp.status_code == 204

    team_resp = await superuser_client.get(f"/api/teams/{USER_TEAM_ID}")
    assert team_resp.status_code == 200


async def test_user_emails_are_stored_and_matched_however_they_are_typed(superuser_client: AsyncClient) -> None:
    create_resp = await superuser_client.post(
        "/api/users",
        json={"name": "Mixed Case", "email": "Mixed.Case@Example.COM", "password": "Test_Password1!"},
    )
    assert create_resp.status_code == 201, create_resp.text
    assert create_resp.json()["email"] == "mixed.case@example.com"

    update_resp = await superuser_client.patch(
        f"/api/users/{create_resp.json()['id']}",
        json={"email": "Renamed.Case@Example.COM"},
    )
    assert update_resp.status_code == 200, update_resp.text
    assert update_resp.json()["email"] == "renamed.case@example.com"

    assign_resp = await superuser_client.post(
        "/api/roles/superuser/assign",
        json={"userName": "RENAMED.CASE@example.com"},
    )
    assert assign_resp.status_code == 201, assign_resp.text


async def test_a_password_sent_with_a_new_email_is_checked_against_the_new_email(superuser_client: AsyncClient) -> None:
    refused = await superuser_client.patch(
        f"/api/users/{REGULAR_USER_ID}",
        json={"email": "renamed.user@example.com", "password": "Renamed.User@Example.com"},
    )

    assert refused.status_code == 400
    assert refused.json()["detail"] == "Password must not be the same as the email address."
    unchanged = await superuser_client.get(f"/api/users/{REGULAR_USER_ID}")
    assert unchanged.json()["email"] == "user@example.com"


async def test_an_account_with_a_password_says_so_in_every_user_response(superuser_client: AsyncClient) -> None:
    responses = {
        "own profile": await superuser_client.get("/api/me"),
        "own profile update": await superuser_client.patch("/api/me", json={"name": "Renamed Superuser"}),
        "user": await superuser_client.get(f"/api/users/{REGULAR_USER_ID}"),
        "user update": await superuser_client.patch(f"/api/users/{REGULAR_USER_ID}", json={"name": "Renamed User"}),
        "admin detail": await superuser_client.get(f"/api/admin/users/{REGULAR_USER_ID}"),
        "admin update": await superuser_client.patch(f"/api/admin/users/{REGULAR_USER_ID}", json={"name": "Renamed"}),
    }
    listed = (await superuser_client.get("/api/users")).json()["items"]

    assert {name: response.json()["hasPassword"] for name, response in responses.items()} == dict.fromkeys(
        responses, True
    )
    assert all(user["hasPassword"] for user in listed)


async def test_an_account_without_a_password_says_so_in_every_user_response(
    superuser_client: AsyncClient,
    session: AsyncSession,
) -> None:
    oauth_only = m.User(email="oauth-only@example.com", name="OAuth Only", is_active=True, is_verified=True)
    session.add(oauth_only)
    await session.commit()

    responses = {
        "user": await superuser_client.get(f"/api/users/{oauth_only.id}"),
        "user update": await superuser_client.patch(f"/api/users/{oauth_only.id}", json={"name": "Renamed User"}),
        "admin detail": await superuser_client.get(f"/api/admin/users/{oauth_only.id}"),
        "admin update": await superuser_client.patch(f"/api/admin/users/{oauth_only.id}", json={"name": "Renamed"}),
    }
    listed = (await superuser_client.get("/api/users")).json()["items"]

    assert {name: response.json()["hasPassword"] for name, response in responses.items()} == dict.fromkeys(
        responses, False
    )
    assert [user["hasPassword"] for user in listed if user["email"] == "oauth-only@example.com"] == [False]


async def test_superuser_role_assignment_grants_and_revokes_team_access(
    seeded_client: AsyncClient,
) -> None:
    """Assigning and revoking the superuser role dynamically updates cross-team access."""
    await login_session_client(seeded_client, "user@example.com", "Test_Password2!")
    initial_teams = await seeded_client.get("/api/teams")
    assert initial_teams.status_code == 200
    assert int(initial_teams.json()["total"]) == 1

    reset_client_session(seeded_client)
    admin_csrf = await login_session_client(seeded_client, "superuser@example.com", "Test_Password1!")
    assign_resp = await seeded_client.post(
        "/api/roles/superuser/assign",
        json={"userName": "user@example.com"},
        headers=admin_csrf,
    )
    assert assign_resp.status_code == 201
    assert assign_resp.json()["message"] == "Successfully assigned the 'superuser' role to user@example.com."

    reset_client_session(seeded_client)
    user_csrf = await login_session_client(seeded_client, "user@example.com", "Test_Password2!")
    patch_other = await seeded_client.patch(
        f"/api/teams/{OTHER_TEAM_ID}",
        json={"name": "Superuser Promoted Update"},
        headers=user_csrf,
    )
    assert patch_other.status_code == 200

    all_teams = await seeded_client.get("/api/teams")
    assert all_teams.status_code == 200
    assert int(all_teams.json()["total"]) == 3

    reset_client_session(seeded_client)
    admin_csrf = await login_session_client(seeded_client, "superuser@example.com", "Test_Password1!")
    revoke_resp = await seeded_client.post(
        "/api/roles/superuser/revoke",
        json={"userName": "user@example.com"},
        headers=admin_csrf,
    )
    assert revoke_resp.status_code == 201

    reset_client_session(seeded_client)
    user_csrf = await login_session_client(seeded_client, "user@example.com", "Test_Password2!")
    blocked_delete = await seeded_client.delete(f"/api/teams/{OTHER_TEAM_ID}", headers=user_csrf)
    assert blocked_delete.status_code == 403

    own_delete = await seeded_client.delete(f"/api/teams/{USER_TEAM_ID}", headers=user_csrf)
    assert own_delete.status_code == 204

    blocked_get = await seeded_client.get(f"/api/teams/{OTHER_TEAM_ID}")
    assert blocked_get.status_code == 403

    final_teams = await seeded_client.get("/api/teams")
    assert final_teams.status_code == 200
    assert int(final_teams.json()["total"]) == 0


async def test_self_service_profile_get_and_update(authenticated_client: AsyncClient) -> None:
    """Authenticated users can inspect and update their own profile via ``/api/me``."""
    me_resp = await authenticated_client.get("/api/me")
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "authuser@example.com"

    patch_resp = await authenticated_client.patch("/api/me", json={"name": "Updated Profile Name"})
    assert patch_resp.status_code == 200
    assert patch_resp.json()["name"] == "Updated Profile Name"

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import pytest
from httpx import Response

if TYPE_CHECKING:
    from httpx import AsyncClient


pytestmark = pytest.mark.anyio


async def test_superuser_role_access(
    client: "AsyncClient",
    user_token_headers: dict[str, str],
    superuser_token_headers: dict[str, str],
) -> None:
    # user should not see all teams to start
    response = await client.get("/api/teams", headers=user_token_headers)
    assert response.status_code == 200
    assert int(response.json()["total"]) == 1

    # assign the role
    response = await client.post(
        "/api/roles/superuser/assign",
        json={"userName": "user@example.com"},
        headers=superuser_token_headers,
    )
    assert response.status_code == 201
    assert response.json()["message"] == "Successfully assigned the 'superuser' role to user@example.com."
    response = await client.patch(
        "/api/teams/81108ac1-ffcb-411d-8b1e-d91833999999",
        json={"name": "TEST UPDATE"},
        headers=user_token_headers,
    )
    assert response.status_code == 200
    # retrieve
    response = await client.get("/api/teams/81108ac1-ffcb-411d-8b1e-d91833999999", headers=user_token_headers)
    assert response.status_code == 200
    response = await client.get("/api/teams", headers=user_token_headers)
    assert response.status_code == 200
    assert int(response.json()["total"]) == 3

    # superuser should see all
    response = await client.get("/api/teams", headers=superuser_token_headers)
    assert response.status_code == 200
    assert int(response.json()["total"]) == 3
    # delete
    # revoke role now
    response = await client.post(
        "/api/roles/superuser/revoke",
        json={"userName": "user@example.com"},
        headers=superuser_token_headers,
    )
    assert response.status_code == 201
    response = await client.delete("/api/teams/81108ac1-ffcb-411d-8b1e-d91833999999", headers=user_token_headers)
    assert response.status_code == 403
    response = await client.delete("/api/teams/97108ac1-ffcb-411d-8b1e-d9183399f63b", headers=user_token_headers)
    assert response.status_code == 204

    # retrieve should now fail
    response = await client.get("/api/teams/81108ac1-ffcb-411d-8b1e-d91833999999", headers=user_token_headers)
    assert response.status_code == 403
    # user should only see 1 now.
    response = await client.get("/api/teams", headers=user_token_headers)
    assert response.status_code == 200
    assert int(response.json()["total"]) == 0


@pytest.mark.parametrize("n_requests", [1, 4])
async def test_assign_role_concurrent(
    client: "AsyncClient",
    superuser_token_headers: dict[str, str],
    n_requests: int,
) -> None:
    async def post() -> Response:
        return await client.post(
            "/api/roles/superuser/assign",
            json={"userName": "user@example.com"},
            headers=superuser_token_headers,
        )

    responses = await asyncio.gather(*[post() for _ in range(n_requests)])

    assert all(res.status_code == 201 for res in responses)
    messages = [res.json()["message"] for res in responses]
    assert "Successfully assigned the 'superuser' role to user@example.com." in messages

    responses = await asyncio.gather(*[post() for _ in range(n_requests)])
    assert all(res.status_code == 201 for res in responses)
    messages = [res.json()["message"] for res in responses]
    assert all(msg == "User user@example.com already has the 'superuser' role." for msg in messages)

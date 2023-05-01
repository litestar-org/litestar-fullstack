from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from httpx import AsyncClient


async def test_update_user_no_auth(client: "AsyncClient") -> None:
    response = await client.patch("/api/users/97108ac1-ffcb-411d-8b1e-d9183399f63b", json={"name": "TEST UPDATE"})
    assert response.status_code == 401


async def test_update_user(client: "AsyncClient", user_token_headers: dict[str, str]) -> None:
    response = await client.patch(
        "/api/users/5ef29f3c-3560-4d15-ba6b-a2e5c721e4d2", json={"name": "TEST UPDATE"}, headers=user_token_headers
    )
    assert response.status_code == 403


async def test_delete_user(client: "AsyncClient", superuser_token_headers: dict[str, str]) -> None:
    response = await client.delete(
        "/api/users/5ef29f3c-3560-4d15-ba6b-a2e5c721e4d2",
        headers=superuser_token_headers,
    )
    assert response.status_code == 204

from typing import TYPE_CHECKING

from httpx import AsyncClient

if TYPE_CHECKING:
    from litestar import Litestar


async def test_update_user_no_auth(app: "Litestar") -> None:
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        response = await client.patch("/api/users/97108ac1-ffcb-411d-8b1e-d9183399f63b", json={"name": "TEST UPDATE"})
        assert response.status_code == 401


async def test_update_user(app: "Litestar", user_token_headers: dict[str, str]) -> None:
    async with AsyncClient(app=app, base_url="http://testserver", headers=user_token_headers) as client:
        response = await client.patch(
            "/api/users/5ef29f3c-3560-4d15-ba6b-a2e5c721e4d2", json={"name": "TEST UPDATE"}, headers=user_token_headers
        )
        assert response.status_code == 403


async def test_update_user_superuser(app: "Litestar", superuser_token_headers: dict[str, str]) -> None:
    async with AsyncClient(app=app, base_url="http://testserver", headers=superuser_token_headers) as client:
        response = await client.patch(
            "/api/users/5ef29f3c-3560-4d15-ba6b-a2e5c721e4d2",
            json={"name": "TEST UPDATE"},
            headers=superuser_token_headers,
        )
        assert response.status_code == 200

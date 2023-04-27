from typing import TYPE_CHECKING

from httpx import AsyncClient

if TYPE_CHECKING:
    from litestar import Litestar


async def test_update_user_no_auth(app: "Litestar") -> None:
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        response = await client.patch("/api/users/97108ac1-ffcb-411d-8b1e-d9183399f63b", json={"name": "TEST UPDATE"})
        assert response.status_code == 401

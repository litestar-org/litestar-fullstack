from starlite import Request
from starlite.contrib.jwt import Token

from app.domain.accounts.models import User


async def provide_user(request: Request[User, Token]) -> User:
    """Get the user from the request.

    Args:
        request: current request.

    Returns:
    User | None
    """
    return request.user

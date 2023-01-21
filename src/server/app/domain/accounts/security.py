# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from __future__ import annotations

from typing import TYPE_CHECKING

from starlite import ASGIConnection, BaseRouteHandler, NotAuthorizedException
from starlite.contrib.jwt import Token

from app.domain.accounts.services import UserService
from app.lib import logging

if TYPE_CHECKING:
    from typing import Any

    from .models import User

logger = logging.getLogger()


__all__ = [
    "current_user_from_token",
    "requires_active_user",
    "requires_superuser",
]


async def current_user_from_token(token: Token, connection: ASGIConnection[Any, Any, Any]) -> User:
    """Current user from local JWT token.

    Fetches the user information from the database when loading from a local token.

    If the user doesn't exist, the record will be created and returned.

    Args:
        unique_identifier (str): _description_
        connection (ASGIConnection[Any, Any, Any]): ASGI connection.

    Raises:
        NotAuthorizedException: User not authorized.

    Returns:
        User: User record mapped to the JWT identifier
    """
    service = UserService()
    user = await service.get(token.sub)
    if user and user.is_active:
        return user
    raise NotAuthorizedException("Unable to authenticate token.")


def requires_active_user(request: ASGIConnection, _: BaseRouteHandler) -> None:
    """Request requires active user.

    Verifies the request user is active.

    Args:
        request (Request): _description_
        _ (BaseRouteHandler): _description_

    Raises:
        NotAuthorizedException: _description_
    """
    if request.user.is_active:
        return
    raise NotAuthorizedException("Inactive account")


def requires_superuser(request: ASGIConnection, _: BaseRouteHandler) -> None:
    """Verifies the request user is a superuser.

    Args:
        request (Request): _description_
        _ (BaseRouteHandler): _description_

    Raises:
        NotAuthorizedException: _description_

    Returns:
        None: _description_
    """
    if request.user.is_superuser:
        return
    raise NotAuthorizedException(detail="Insufficient privileges")

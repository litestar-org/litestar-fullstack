# pylint: disable=[invalid-name,import-outside-toplevel]
# SPDX-FileCopyrightText: 2023-present Cody Fincher <cody.fincher@gmail.com>
#
# SPDX-License-Identifier: MIT
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from litestar import Litestar


def create_app() -> Litestar:
    """Create ASGI application."""

    from litestar import Litestar
    from litestar.di import Provide

    from app.config import app as config
    from app.config import constants
    from app.config.base import get_settings
    from app.domain.accounts import signals as account_signals
    from app.domain.accounts.dependencies import provide_user
    from app.domain.teams import signals as team_signals
    from app.lib.dependencies import create_collection_dependencies
    from app.server import openapi, plugins, routers

    dependencies = {constants.USER_DEPENDENCY_KEY: Provide(provide_user)}
    dependencies.update(create_collection_dependencies())
    settings = get_settings()

    return Litestar(
        cors_config=config.cors,
        csrf_config=config.csrf,
        dependencies=dependencies,
        debug=settings.app.DEBUG,
        openapi_config=openapi.config,
        route_handlers=routers.route_handlers,
        plugins=[
            plugins.app_config,
            plugins.structlog,
            plugins.alchemy,
            plugins.vite,
            plugins.saq,
            plugins.granian,
            plugins.inertia,
            plugins.flasher,
        ],
        listeners=[account_signals.user_created_event_handler, team_signals.team_created_event_handler],
    )


app = create_app()

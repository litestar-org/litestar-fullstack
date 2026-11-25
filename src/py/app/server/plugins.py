"""First-party Litestar plugin stack assembly."""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING, Any

from advanced_alchemy.extensions.litestar import SQLAlchemyPlugin
from litestar.plugins.problem_details import ProblemDetailsPlugin
from litestar.plugins.structlog import StructlogPlugin
from litestar_asyncapi import AsyncAPIPlugin
from litestar_autowire import AutowirePlugin
from litestar_email import EmailPlugin
from litestar_granian import GranianPlugin
from litestar_mcp import LitestarMCP
from litestar_queues import QueuePlugin
from litestar_security import SecurityPlugin
from litestar_vite import VitePlugin

from app import config
from app.lib.settings import get_settings

if TYPE_CHECKING:
    from litestar.plugins import PluginProtocol
    from litestar_autowire import AutowireConfig
    from litestar_email import EmailConfig
    from litestar_mcp import MCPConfig
    from litestar_queues import QueueConfig
    from litestar_security import SecurityConfig

__all__ = ("build_plugins",)


def build_plugins(
    *,
    autowire_config: AutowireConfig | None = None,
    security_config: SecurityConfig[Any] | None = None,
    queue_config: QueueConfig | None = None,
    mcp_config: MCPConfig | None = None,
    email_config: EmailConfig | None = None,
) -> list[PluginProtocol]:
    """Build the 11 first-party Litestar plugins in deterministic registration order.

    ``SecurityPlugin`` is always registered last so it compiles routes emitted by
    ``QueuePlugin``, ``AsyncAPIPlugin``, ``VitePlugin``, ``LitestarMCP``, and
    ``AutowirePlugin``.

    Returns:
        Ordered list of configured Litestar plugins.
    """
    resolved_email = email_config or config.email
    if resolved_email.email_service_dependency_key == "mailer":
        resolved_email = replace(resolved_email, email_service_dependency_key="email_service_provider")
    plugins: list[PluginProtocol] = [
        StructlogPlugin(config=config.log),
        GranianPlugin(static="auto"),
        SQLAlchemyPlugin(config=config.alchemy),
        EmailPlugin(config=resolved_email),
        QueuePlugin(config=queue_config or config.queues),
        AsyncAPIPlugin(config=config.asyncapi),
        VitePlugin(config=config.vite),
    ]
    if mcp_config is not None or get_settings().mcp.ENABLED:
        plugins.append(LitestarMCP(config=mcp_config or config.mcp))
    plugins.extend(
        [
            AutowirePlugin(config=autowire_config or config.autowire),
            ProblemDetailsPlugin(config=config.problem_details),
            SecurityPlugin(config=security_config or config.security),
        ]
    )
    return plugins

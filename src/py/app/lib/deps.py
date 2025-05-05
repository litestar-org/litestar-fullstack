"""Application dependency providers generators.

This module contains functions to create dependency providers for services and filters.

You should not have modify this module very often and should only be invoked under normal usage.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from advanced_alchemy.extensions.litestar.providers import (
    create_filter_dependencies,
    create_service_dependencies,
    create_service_provider,
)

if TYPE_CHECKING:
    from saq import Queue

__all__ = ("create_filter_dependencies", "create_service_dependencies", "create_service_provider", "get_task_queue")


async def get_task_queue() -> Queue:
    """Get Queues

    Returns:
        dict[str,Queue]: A list of queues
    """
    from app.server import plugins

    task_queues = plugins.saq.get_queue("background-tasks")
    await task_queues.connect()

    return task_queues

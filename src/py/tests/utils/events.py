"""Test utilities for event handling."""

from __future__ import annotations

import asyncio


async def wait_for_events(max_wait: float = 1.0, interval: float = 0.1) -> None:
    """Wait for async event listeners to complete.

    This function allows async event handlers to process by yielding
    control to the event loop multiple times.

    Args:
        max_wait: Maximum time to wait in seconds.
        interval: Time between yields in seconds.
    """
    elapsed = 0.0
    while elapsed < max_wait:
        await asyncio.sleep(interval)
        elapsed += interval

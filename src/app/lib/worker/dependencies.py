from __future__ import annotations

from typing import TYPE_CHECKING

from .base import Queue, queues

if TYPE_CHECKING:
    from collections.abc import Generator


def provide_queues() -> Generator[dict[str, Queue], None, None]:
    yield queues

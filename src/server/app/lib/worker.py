import atexit
import signal
import threading
from multiprocessing.util import _exit_function  # type: ignore[attr-defined]
from typing import Any

import anyio
from anyio import create_task_group, open_signal_receiver
from anyio.abc import CancelScope
from starlite_saqlalchemy import log
from starlite_saqlalchemy.worker import (
    JobConfig,
    Queue,
    Worker,
    create_worker_instance,
    default_job_config_dict,
    enqueue_background_task_for_service,
    make_service_callback,
    queue,
)

from . import logging

__all__ = [
    "JobConfig",
    "Queue",
    "Worker",
    "create_worker_instance",
    "default_job_config_dict",
    "make_service_callback",
    "enqueue_background_task_for_service",
    "queue",
    "run_worker",
]

logger = logging.getLogger()

if threading.current_thread() is not threading.main_thread():
    atexit.unregister(_exit_function)


def run_worker() -> None:
    """Run a worker."""
    anyio.run(_run_worker, backend="asyncio", backend_options={"use_uvloop": True})


async def _signal_handler(scope: CancelScope, worker_instance: Worker) -> None:
    with open_signal_receiver(signal.SIGINT, signal.SIGTERM) as signals:
        async for _ in signals:
            await worker_instance.stop()
            scope.cancel()
            return


async def _run_worker() -> None:
    async with create_task_group() as tg:

        worker_kwargs: dict[str, Any] = {"functions": [(make_service_callback.__qualname__, make_service_callback)]}
        worker_kwargs["before_process"] = log.worker.before_process
        worker_kwargs["after_process"] = log.worker.after_process
        worker_instance = create_worker_instance(**worker_kwargs)
        tg.start_soon(_signal_handler, tg.cancel_scope, worker_instance)

        await worker_instance.start()

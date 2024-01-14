import asyncio

from saq.types import Context
from structlog import get_logger

__all__ = ["background_worker_task", "system_task", "system_upkeep"]


logger = get_logger()


async def system_upkeep(_: Context) -> None:
    await logger.ainfo("Performing system upkeep operations.")
    await logger.ainfo("Simulating a long running operation.  Sleeping for 60 seconds.")
    await asyncio.sleep(60)
    await logger.ainfo("Simulating an even long running operation.  Sleeping for 120 seconds.")
    await asyncio.sleep(120)
    await logger.ainfo("Long running process complete.")
    await logger.ainfo("Performing system upkeep operations.")


async def background_worker_task(_: Context) -> None:
    await logger.ainfo("Performing background worker task.")
    await asyncio.sleep(20)
    await logger.ainfo("Performing system upkeep operations.")


async def system_task(_: Context) -> None:
    await logger.ainfo("Performing simple system task")
    await asyncio.sleep(2)
    await logger.ainfo("System task complete.")

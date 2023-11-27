from __future__ import annotations

import asyncio
import os
import re
import subprocess
import timeit
from typing import TYPE_CHECKING, Any

import asyncpg
import pytest
from litestar.utils.sync import AsyncCallable
from redis.asyncio import Redis as AsyncRedis
from redis.exceptions import ConnectionError as RedisConnectionError

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable


pytestmark = pytest.mark.anyio


async def wait_until_responsive(
    check: Callable[..., Awaitable],
    timeout: float,
    pause: float,
    **kwargs: Any,
) -> None:
    """Wait until a service is responsive.

    Args:
        check: Coroutine, return truthy value when waiting should stop.
        timeout: Maximum seconds to wait.
        pause: Seconds to wait between calls to `check`.
        **kwargs: Given as kwargs to `check`.
    """
    ref = timeit.default_timer()
    now = ref
    while (now - ref) < timeout:  # sourcery skip
        if await check(**kwargs):
            return
        await asyncio.sleep(pause)
        now = timeit.default_timer()

    msg = "Timeout reached while waiting on service!"
    raise RuntimeError(msg)


class DockerServiceRegistry:
    def __init__(self, use_legacy_compose: bool = False) -> None:
        self._use_legacy_compose = use_legacy_compose
        if os.environ.get("DOCKER_USE_LEGACY_COMPOSE") == "true":
            self._use_legacy_compose = True
        self._running_services: set[str] = set()
        self.docker_ip = self._get_docker_ip()
        self._base_command = ["docker-compose"] if self._use_legacy_compose else ["docker", "compose"]
        self._base_command.extend(
            [
                "--file=tests/docker-compose.yml",
                "--project-name=app_pytest",
            ],
        )

    def _get_docker_ip(self) -> str:
        docker_host = os.environ.get("DOCKER_HOST", "").strip()
        if not docker_host or docker_host.startswith("unix://"):
            return "127.0.0.1"

        if match := re.match(r"^tcp://(.+?):\d+$", docker_host):
            return match[1]

        msg = f'Invalid value for DOCKER_HOST: "{docker_host}".'
        raise ValueError(msg)

    def run_command(self, *args: str) -> None:
        command = [*self._base_command, *args]
        subprocess.run(command, check=True, capture_output=True)

    async def start(
        self,
        name: str,
        *,
        check: Callable[..., Awaitable],
        timeout: float = 30,
        pause: float = 0.1,
        **kwargs: Any,
    ) -> None:
        if name not in self._running_services:
            run_command = ["up", "-d", name]
            if not self._use_legacy_compose:
                run_command.append("--wait")
            self.run_command(*run_command)
            self._running_services.add(name)

            await wait_until_responsive(
                check=AsyncCallable(check),
                timeout=timeout,
                pause=pause,
                host=self.docker_ip,
                **kwargs,
            )

    def stop(self, name: str) -> None:
        pass

    def down(self) -> None:
        self.run_command("down", "-t", "5")


async def redis_responsive(host: str) -> bool:
    client: AsyncRedis = AsyncRedis(host=host, port=6397)
    try:
        return await client.ping()
    except (ConnectionError, RedisConnectionError):
        return False
    finally:
        await client.aclose()  # type: ignore[attr-defined]


async def postgres_responsive(host: str) -> bool:
    try:
        conn = await asyncpg.connect(
            host=host,
            port=5423,
            user="postgres",
            database="postgres",
            password="super-secret",  # noqa: S106
        )
    except (ConnectionError, asyncpg.CannotConnectNowError):
        return False

    try:
        return (await conn.fetchrow("SELECT 1"))[0] == 1  # type: ignore
    finally:
        await conn.close()

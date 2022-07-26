# -*- coding: utf-8 -*-
"""Application Web Server Gateway Interface - gunicorn."""
import asyncio
import os
import signal
import sys
import threading
import time
from typing import Any

from gunicorn.app.base import Application
from gunicorn.arbiter import Arbiter
from uvicorn.main import Server
from uvicorn.workers import UvicornWorker as _UvicornWorker

from pyspa.config import settings
from pyspa.core.asgi import app


class ReloaderThread(threading.Thread):
    def __init__(self, worker: "UvicornWorker", sleep_interval: float = 1.0):
        super().__init__()
        self.daemon = True
        self._worker = worker
        self._interval = sleep_interval

    def run(self) -> None:
        """
        Sends a KILL signal to the current process if the worker's active flag is set to
        False.
        """
        while True:
            if not self._worker.alive:
                os.kill(os.getpid(), signal.SIGINT)
            time.sleep(self._interval)


class UvicornWorker(_UvicornWorker):  # type: ignore
    CONFIG_KWARGS = {"loop": "uvloop", "http": "httptools", "lifespan": "auto"}

    def __init__(self, *args: list[Any], **kwargs: dict[str, Any]):
        super().__init__(*args, **kwargs)
        self._reloader_thread = ReloaderThread(self)

    def run(self) -> None:
        if self.cfg.reload:
            self._reloader_thread.start()
        super().run()

    def _install_sigquit_handler(self, server: Server) -> None:
        """Workaround to install a SIGQUIT handler on workers.
        Ref.:
        - https://github.com/encode/uvicorn/issues/1116
        - https://github.com/benoitc/gunicorn/issues/2604
        """
        if threading.current_thread() is not threading.main_thread():
            # Signals can only be listened to from the main thread.
            return

        loop = asyncio.get_running_loop()
        loop.add_signal_handler(signal.SIGQUIT, self.handle_exit, signal.SIGQUIT, None)

    async def _serve(self) -> None:
        self.config.app = self.wsgi
        server = Server(config=self.config)
        self._install_sigquit_handler(server)
        await server.serve(sockets=self.sockets)
        if not server.started:
            sys.exit(Arbiter.WORKER_BOOT_ERROR)


class ApplicationLoader(Application):  # type: ignore
    """Bootstraps the WSGI app"""

    def __init__(
        self,
        options=None,
    ):
        self.options = options or {}
        self.config_path = self.options.pop("config", None)
        super().__init__()

    def init(self, parser, options, args):
        """Class ApplicationLoader object constructor."""
        self.options = options
        self.cfg.set("default_proc_name", args[0])

    def load_config(self):
        """Load config from passed options"""
        if self.config_path:
            self.load_config_from_file(self.config_path)
        config = {
            key: value
            for key, value in self.options.items()
            if key in self.cfg.settings and value is not None
        }
        for key, value in config.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        """Load application."""
        return app


def run_wsgi(
    host: str,
    port: int,
    http_workers: int,
    reload: bool,
):
    """Run gunicorn WSGI with ASGI workers."""
    sys.argv = [
        "--gunicorn",
    ]
    if reload:
        sys.argv.append("-r")
    sys.argv.append("opdba.core.asgi:app")
    ApplicationLoader(
        options={
            "host": host,
            "workers": str(http_workers),
            "port": str(port),
            "reload": reload,
            "loglevel": settings.app.LOG_LEVEL,
            "config": "opdba/config/gunicorn.py",
        },
    ).run()


if __name__ == "__main__":

    run_wsgi(
        host=settings.server.bind_host,
        port=settings.server.tcp_port,
        http_workers=settings.server.http_workers,
        reload=settings.server.reload,
    )

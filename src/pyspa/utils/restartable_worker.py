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
from uvicorn.workers import UvicornWorker


class ReloaderThread(threading.Thread):
    def __init__(self, worker: UvicornWorker, sleep_interval: float = 1.0):
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


class RestartableUvicornWorker(UvicornWorker):  # type: ignore
    """
    UvicornWorker with additional thread that sends a KILL signal to the current process
    if the worker's active flag is set to False.

    attribution: https://github.com/benoitc/gunicorn/issues/2339#issuecomment-867481389
    """

    CONFIG_KWARGS = {"loop": "uvloop", "http": "httptools", "lifespan": "auto"}

    def __init__(self, *args: list[Any], **kwargs: dict[str, Any]):
        super().__init__(*args, **kwargs)
        self._reloader_thread = ReloaderThread(self)

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

    def run(self) -> None:
        if self.cfg.reload:
            self._reloader_thread.start()
        super().run()


class ApplicationLoader(Application):  # type: ignore
    """Bootstraps the WSGI app"""

    def __init__(self, options: dict[str, str] | None = None):
        self.options = options or {}
        self.config_path = self.options.pop("config", None)
        super().__init__()

    def init(self, parser, options, args) -> None:  # type: ignore
        """Class ApplicationLoader object constructor."""
        self.options = options
        self.cfg.set("default_proc_name", args[0])

    def load_config(self) -> None:
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
        return get_app()

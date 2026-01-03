import multiprocessing
import platform

from app import cli, config, db, domain, lib, server, utils

__all__ = (
    "cli",
    "config",
    "db",
    "domain",
    "lib",
    "server",
    "utils",
)

if platform.system() == "Darwin":
    multiprocessing.set_start_method("fork", force=True)

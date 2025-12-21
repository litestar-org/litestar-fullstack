import multiprocessing
import platform

from app import cli, config, db, domain, lib, schemas, server, utils

__all__ = (
    "cli",
    "config",
    "db",
    "domain",
    "lib",
    "schemas",
    "server",
    "utils",
)

if platform.system() == "Darwin":
    multiprocessing.set_start_method("fork", force=True)

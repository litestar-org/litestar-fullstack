"""Litestar fullstack SPA reference application package."""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app import cli, config, db, domain, lib, server, utils

_SUBMODULES = frozenset({"cli", "config", "db", "domain", "lib", "server", "utils"})

__all__ = (
    "cli",
    "config",
    "db",
    "domain",
    "lib",
    "server",
    "utils",
)


def __getattr__(name: str) -> Any:
    """Lazily load top-level application subpackages on attribute access.

    Returns:
        Imported ``app.<name>`` subpackage module.

    Raises:
        AttributeError: If ``name`` is not an exported top-level subpackage.
    """
    if name in _SUBMODULES:
        return import_module(f"app.{name}")
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)

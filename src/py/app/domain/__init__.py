"""Application domain packages discovered by ``AutowirePlugin``."""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.domain import accounts, admin, system, tags, teams

_SUBMODULES = frozenset({"accounts", "admin", "system", "tags", "teams"})

__all__ = ("accounts", "admin", "system", "tags", "teams")


def __getattr__(name: str) -> Any:
    """Lazily load domain subpackages on attribute access."""
    if name in _SUBMODULES:
        return import_module(f"app.domain.{name}")
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)

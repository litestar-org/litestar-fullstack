"""Admin domain module."""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.domain.admin import controllers, deps, schemas, services

__all__ = ("controllers", "deps", "schemas", "services")


def __getattr__(name: str) -> Any:
    """Lazily load admin domain submodules on attribute access.

    Returns:
        The imported admin submodule.

    Raises:
        AttributeError: If ``name`` is not an exported admin submodule.
    """
    if name in __all__:
        return import_module(f"app.domain.admin.{name}")
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)

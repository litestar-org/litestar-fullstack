"""Accounts domain package."""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.domain.accounts import controllers, deps, schemas, security, services

__all__ = (
    "controllers",
    "deps",
    "schemas",
    "security",
    "services",
)


def __getattr__(name: str) -> Any:
    """Lazily load accounts submodules on attribute access."""
    if name in __all__:
        return import_module(f"app.domain.accounts.{name}")
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)

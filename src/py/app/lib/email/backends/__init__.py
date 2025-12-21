"""Email backend registry for extensible backend system.

This module provides a registry pattern for email backends, allowing
new backends to be added without modifying core code. Backends can be
registered using the @register_backend decorator or loaded dynamically
from a full Python path.

Example:
    # Register a custom backend
    @register_backend("custom")
    class CustomBackend(BaseEmailBackend):
        ...

    # Get backend by short name
    backend_class = get_backend_class("custom")

    # Get backend by full path
    backend_class = get_backend_class("myapp.backends.CustomBackend")

    # Get configured backend instance
    backend = get_backend()
"""

from __future__ import annotations

from functools import lru_cache
from importlib import import_module
from typing import TYPE_CHECKING, Any, TypeVar

if TYPE_CHECKING:
    from collections.abc import Callable

    from app.lib.email.backends.base import BaseEmailBackend

# Registry of available backends (populated at import time)
_backend_registry: dict[str, type[BaseEmailBackend]] = {}

T = TypeVar("T", bound="BaseEmailBackend")


def register_backend(name: str) -> Callable[[type[T]], type[T]]:
    """Decorator to register an email backend.

    This decorator registers a backend class with a short name that can be
    used in settings configuration instead of the full Python path.

    Args:
        name: Short name for the backend (e.g., "smtp", "console").

    Returns:
        Decorator function that registers the backend class.

    Example:
        @register_backend("smtp")
        class AsyncSMTPBackend(BaseEmailBackend):
            ...

        # Can now use EMAIL_BACKEND=smtp in settings
    """

    def decorator(cls: type[T]) -> type[T]:
        _backend_registry[name] = cls
        return cls

    return decorator


def get_backend_class(backend_path: str) -> type[BaseEmailBackend]:
    """Get backend class from dotted path or short name.

    This function supports two formats:
    1. Short names registered via @register_backend (e.g., "smtp", "console")
    2. Full Python paths (e.g., "app.lib.email.backends.smtp.AsyncSMTPBackend")

    Args:
        backend_path: Either a full path like "app.lib.email.backends.smtp.AsyncSMTPBackend"
                      or a short name like "smtp".

    Returns:
        The backend class.

    Raises:
        ImportError: If backend cannot be found by path.
        KeyError: If short name is not registered.
    """
    # Ensure builtins are registered
    _register_builtins()

    # Check registry first (short names)
    if backend_path in _backend_registry:
        return _backend_registry[backend_path]

    # Otherwise, import from full path
    if "." not in backend_path:
        msg = f"Unknown email backend: {backend_path!r}. Available: {list(_backend_registry.keys())}"
        raise KeyError(msg)

    module_path, class_name = backend_path.rsplit(".", 1)
    module = import_module(module_path)
    return getattr(module, class_name)  # type: ignore[no-any-return]


def list_backends() -> dict[str, type[BaseEmailBackend]]:
    """List all registered backends.

    Returns:
        Dictionary mapping short names to backend classes.
    """
    _register_builtins()
    return _backend_registry.copy()


@lru_cache(maxsize=1)
def _register_builtins() -> None:
    """Import built-in backends to trigger registration.

    This is called lazily to avoid import cycles.
    """
    from app.lib.email.backends import console, locmem, smtp


def get_backend(fail_silently: bool = False, **kwargs: Any) -> BaseEmailBackend:
    """Get an instance of the configured email backend.

    This function creates a backend instance using the EMAIL_BACKEND setting.
    Additional keyword arguments are passed to the backend constructor.

    Args:
        fail_silently: If True, suppress exceptions during send operations.
        **kwargs: Additional arguments passed to backend constructor.

    Returns:
        Configured backend instance.

    Example:
        # Get default backend
        backend = get_backend()
        await backend.send_messages([message])

        # Get backend with custom settings
        backend = get_backend(fail_silently=True, timeout=60)
    """
    from app.lib.settings import get_settings

    settings = get_settings()
    backend_path = settings.email.BACKEND
    backend_class = get_backend_class(backend_path)
    return backend_class(fail_silently=fail_silently, **kwargs)

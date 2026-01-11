"""Discovery logic for domain components."""

from __future__ import annotations

import importlib
import inspect
import pkgutil
from pathlib import Path
from typing import TYPE_CHECKING

import structlog
from litestar import Controller

from app.utils.domain._state import cache

if TYPE_CHECKING:
    from collections.abc import Generator

    from litestar.events import EventListener

logger = structlog.get_logger()


def find_controllers_in_module(module: object) -> list[type[Controller]]:
    """Find all Controller subclasses defined in a module.

    Only returns controllers that are defined in the module itself,
    not imported from elsewhere.

    Args:
        module: The module to inspect for controllers.

    Returns:
        List of Controller subclasses defined in the module.
    """
    controllers: list[type[Controller]] = []
    module_name = getattr(module, "__name__", "")

    for name, obj in inspect.getmembers(module, inspect.isclass):
        # Skip the Controller base class itself
        if obj is Controller:
            continue

        # Check if it's a Controller subclass
        if not issubclass(obj, Controller):
            continue

        # Only include controllers defined in this module (not imported)
        if getattr(obj, "__module__", None) != module_name:
            continue

        # Skip private classes
        if name.startswith("_"):
            continue

        controllers.append(obj)

    return controllers


def _iter_domain_directories(domain_pkg: str) -> list[tuple[str, Path]]:
    """Iterate through domain subdirectories in a package.

    Args:
        domain_pkg: The domain package path (e.g., "app.domain").

    Returns:
        List of (domain_module_path, domain_dir) tuples.
    """
    try:
        base_module = importlib.import_module(domain_pkg)
    except ImportError:
        logger.warning("Domain package not found", package=domain_pkg)
        return []

    if not hasattr(base_module, "__path__"):
        logger.warning("Package has no __path__", package=domain_pkg)
        return []

    base_path = Path(str(base_module.__path__[0]))
    results: list[tuple[str, Path]] = []

    if not base_path.exists():
        return []

    for domain_dir in sorted(base_path.iterdir()):
        if not domain_dir.is_dir():
            continue
        if domain_dir.name.startswith(("_", ".")):
            continue

        domain_module_path = f"{domain_pkg}.{domain_dir.name}"
        results.append((domain_module_path, domain_dir))

    return results


def _iter_submodules(domain_packages: list[str], submodules: list[str]) -> Generator[str, None, None]:
    """Iterate over submodules within domain packages.

    Yields:
        Full module path string.
    """
    for domain_pkg in domain_packages:
        for domain_module_path, _ in _iter_domain_directories(domain_pkg):
            for submodule_name in submodules:
                yield f"{domain_module_path}.{submodule_name}"


def _discover_controllers_in_submodule(controller_module_path: str) -> list[type[Controller]]:
    """Discover controllers in a single submodule path.

    Args:
        controller_module_path: The full module path to search.

    Returns:
        List of discovered controllers.
    """
    try:
        controller_module = importlib.import_module(controller_module_path)
    except ImportError:
        return []

    all_controllers: list[type[Controller]] = []

    # If it's a package, walk through all modules in it
    if hasattr(controller_module, "__path__"):
        for _, modname, ispkg in pkgutil.walk_packages(controller_module.__path__, prefix=f"{controller_module_path}."):
            if ispkg:
                continue
            try:
                mod = importlib.import_module(modname)
                controllers = find_controllers_in_module(mod)
                all_controllers.extend(controllers)
            except (ImportError, AttributeError, SyntaxError) as e:
                logger.warning("Failed to import controller module", module=modname, error=str(e))

    # Also check the __init__.py of the package/module itself
    controllers = find_controllers_in_module(controller_module)
    all_controllers.extend(controllers)

    return all_controllers


def discover_domain_controllers(
    domain_packages: list[str], controller_submodules: list[str] | None = None
) -> list[type[Controller]]:
    """Discover controllers in domain subpackages.

    Args:
        domain_packages: List of packages to scan (e.g., ["app.domain"]).
        controller_submodules: List of submodule names to search for controllers.

    Returns:
        List of discovered Controller classes.
    """
    if cache.is_cached(domain_packages):
        cached = cache.get()
        if cached is not None:
            return cached

    if controller_submodules is None:
        controller_submodules = ["controllers", "routes", "controller", "route"]

    all_controllers: list[type[Controller]] = []

    for controller_path in _iter_submodules(domain_packages, controller_submodules):
        controllers = _discover_controllers_in_submodule(controller_path)
        all_controllers.extend(controllers)

    # Deduplicate while preserving order
    seen: set[type[Controller]] = set()
    unique_controllers: list[type[Controller]] = []
    for ctrl in all_controllers:
        if ctrl not in seen:
            seen.add(ctrl)
            unique_controllers.append(ctrl)

    # Cache results
    cache.set(unique_controllers, domain_packages)

    return unique_controllers


def discover_domain_signals(
    domain_packages: list[str], signal_submodules: list[str] | None = None
) -> list[EventListener]:
    """Discover signals/listeners in domain subpackages.

    Args:
        domain_packages: List of packages to scan (e.g., ["app.domain"]).
        signal_submodules: List of submodule names to search for signals.

    Returns:
        List of discovered signal/listener objects.
    """
    if signal_submodules is None:
        signal_submodules = ["signals", "events", "listeners"]

    all_signals: list[EventListener] = []

    for signal_path in _iter_submodules(domain_packages, signal_submodules):
        try:
            module = importlib.import_module(signal_path)
            if hasattr(module, "__all__"):
                for name in module.__all__:
                    obj = getattr(module, name)
                    all_signals.append(obj)
        except ImportError:
            continue
    return all_signals


def discover_domain_schemas(
    domain_packages: list[str], schema_submodules: list[str] | None = None
) -> dict[str, object]:
    """Discover schemas for signature namespace.

    Args:
        domain_packages: List of packages to scan (e.g., ["app.domain"]).
        schema_submodules: List of submodule names to search for schemas.

    Returns:
        Dictionary of discovered schemas suitable for signature namespace.
    """
    if schema_submodules is None:
        schema_submodules = ["schemas", "models", "dtos"]

    all_schemas: dict[str, object] = {}

    for schema_path in _iter_submodules(domain_packages, schema_submodules):
        try:
            module = importlib.import_module(schema_path)
            if hasattr(module, "__all__"):
                for name in module.__all__:
                    obj = getattr(module, name)
                    all_schemas[name] = obj
        except ImportError:
            continue
    return all_schemas


def discover_domain_services(
    domain_packages: list[str], service_submodules: list[str] | None = None
) -> dict[str, object]:
    """Discover services for signature namespace.

    Args:
        domain_packages: List of packages to scan (e.g., ["app.domain"]).
        service_submodules: List of submodule names to search for services.

    Returns:
        Dictionary of discovered services for signature namespace.
    """
    if service_submodules is None:
        service_submodules = ["services"]

    all_services: dict[str, object] = {}

    for service_path in _iter_submodules(domain_packages, service_submodules):
        try:
            module = importlib.import_module(service_path)
            if hasattr(module, "__all__"):
                for name in module.__all__:
                    obj = getattr(module, name)
                    all_services[name] = obj
        except ImportError:
            continue
    return all_services


def discover_domain_repositories(
    domain_packages: list[str], repository_submodules: list[str] | None = None
) -> dict[str, object]:
    """Discover repositories for signature namespace.

    Args:
        domain_packages: List of packages to scan (e.g., ["app.domain"]).
        repository_submodules: List of submodule names to search for repositories.

    Returns:
        Dictionary of discovered repositories for signature namespace.
    """
    if repository_submodules is None:
        repository_submodules = ["repositories", "repos"]

    all_repositories: dict[str, object] = {}

    for repo_path in _iter_submodules(domain_packages, repository_submodules):
        try:
            module = importlib.import_module(repo_path)
            if hasattr(module, "__all__"):
                for name in module.__all__:
                    obj = getattr(module, name)
                    all_repositories[name] = obj
        except ImportError:
            continue
    return all_repositories

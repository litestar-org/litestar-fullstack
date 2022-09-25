"""
All configuration is via environment variables.

Take not of the environment variable prefixes required for each settings class, except
[`AppSettings`][starlite_bedrock.config.AppSettings].
"""
import pkgutil
import sys
from functools import lru_cache
from importlib import import_module
from importlib.machinery import SourceFileLoader
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from types import ModuleType


@lru_cache
def module_to_os_path(dotted_path: str) -> Path:
    """
    Returns the path to the base directory of the project or the module specified by `dotted_path`.

    Ensures that pkgutil returns a valid source file loader.
    """
    src = pkgutil.get_loader(dotted_path)
    if not isinstance(src, SourceFileLoader):
        raise ValueError(f"Couldn't find the path for {dotted_path}")
    return Path(str(src.path).removesuffix("/__init__.py"))


def _is_loaded(module: Optional["ModuleType"]) -> bool:
    spec = getattr(module, "__spec__", None)
    initializing = getattr(spec, "_initializing", False)
    return bool(module and spec and not initializing)


def _cached_import(module_path: str, class_name: str) -> Any:
    """Import and cache a class from a module.
    Args:
        module_path (str): dotted path to module.
        class_name (str): Class or function name.
    Returns:
        object: The imported class or function
    """
    # Check whether module is loaded and fully initialized.
    module = sys.modules.get(module_path)
    if not _is_loaded(module):
        module = import_module(module_path)
    return getattr(module, class_name)  #


def import_string(dotted_path: str) -> Any:
    """Dotted Path Import.
    Import a dotted module path and return the attribute/class designated by the
    last name in the path. Raise ImportError if the import failed.
    Args:
        dotted_path (str): The path of the module to import.
    Raises:
        ImportError: Could not import the module.
    Returns:
        object: The imported object.
    """

    try:
        module_path, class_name = dotted_path.rsplit(".", 1)
    except ValueError as e:
        raise ImportError(f"{dotted_path} doesn't look like a module path") from e

    try:
        return _cached_import(module_path, class_name)
    except AttributeError as e:
        raise ImportError(f"Module '{module_path}' does not define a '{class_name}' attribute/class") from e

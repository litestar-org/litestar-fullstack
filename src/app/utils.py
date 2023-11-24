"""General utility functions."""
from __future__ import annotations

import dataclasses
import pkgutil
import platform
import re
import sys
import unicodedata
from functools import lru_cache
from importlib import import_module
from importlib.machinery import SourceFileLoader
from pathlib import Path
from typing import TYPE_CHECKING, Any

__all__ = [
    "camel_case",
    "case_insensitive_string_compare",
    "check_email",
    "dataclass_as_dict_shallow",
    "import_string",
    "module_to_os_path",
    "slugify",
]


if TYPE_CHECKING:
    from types import ModuleType


def check_email(email: str) -> str:
    """Validate an email."""
    if "@" not in email:
        msg = "Invalid email!"
        raise ValueError(msg)
    return email.lower()


def slugify(value: str, allow_unicode: bool = False, separator: str | None = None) -> str:
    """slugify.

    Convert to ASCII if ``allow_unicode`` is ``False``. Convert spaces or repeated
    dashes to single dashes. Remove characters that aren't alphanumerics,
    underscores, or hyphens. Convert to lowercase. Also strip leading and
    trailing whitespace, dashes, and underscores.

    Args:
        value (str): the string to slugify
        allow_unicode (bool, optional): allow unicode characters in slug. Defaults to False.
        separator (str, optional): by default a `-` is used to delimit word boundaries.
            Set this to configure something different.

    Returns:
        str: a slugified string of the value parameter
    """
    if allow_unicode:
        value = unicodedata.normalize("NFKC", value)
    else:
        value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^\w\s-]", "", value.lower())
    if separator is not None:
        return re.sub(r"[-\s]+", "-", value).strip("-_").replace("-", separator)
    return re.sub(r"[-\s]+", "-", value).strip("-_")


def camel_case(string: str) -> str:
    """Convert a string to camel case.

    Args:
        string (str): The string to convert

    Returns:
        str: The string converted to camel case
    """
    return "".join(word if index == 0 else word.capitalize() for index, word in enumerate(string.split("_")))


def case_insensitive_string_compare(a: str, b: str, /) -> bool:
    """Compare `a` and `b`, stripping whitespace and ignoring case."""
    return a.strip().lower() == b.strip().lower()


def dataclass_as_dict_shallow(dataclass: Any, *, exclude_none: bool = False) -> dict[str, Any]:
    """Convert a dataclass to dict, without deepcopy.

    Args:
        dataclass (Any): The dataclass to convert.
        exclude_none (bool, optional): Exclude None values. Defaults to False.

    Returns:
        dict[str, Any]: The dataclass as a dict.
    """
    ret: dict[str, Any] = {}
    for field in dataclasses.fields(dataclass):
        value = getattr(dataclass, field.name)
        if exclude_none and value is None:
            continue
        ret[field.name] = value
    return ret


@lru_cache
def module_to_os_path(dotted_path: str = "app") -> Path:
    """Find Module to OS Path.

    Return a path to the base directory of the project or the module
    specified by `dotted_path`.

    Ensures that ``pkgutil`` returns a valid source file loader.

    Args:
        dotted_path (str, optional): The path to the module. Defaults to "app".

    Raises:
        TypeError: The module could not be found.

    Returns:
        Path: The path to the module.
    """
    src = pkgutil.get_loader(dotted_path)
    if not isinstance(src, SourceFileLoader):
        msg = "Couldn't find the path for %s"
        raise TypeError(msg, dotted_path)
    path_separator = "\\" if platform.system() == "Windows" else "/"
    return Path(str(src.path).removesuffix(f"{path_separator}__init__.py"))


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

    def _is_loaded(module: ModuleType | None) -> bool:
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
        return getattr(module, class_name)

    try:
        module_path, class_name = dotted_path.rsplit(".", 1)
    except ValueError as e:
        msg = "%s doesn't look like a module path"
        raise ImportError(msg, dotted_path) from e

    try:
        return _cached_import(module_path, class_name)
    except AttributeError as e:
        msg = "Module '%s' does not define a '%s' attribute/class"
        raise ImportError(msg, module_path, class_name) from e

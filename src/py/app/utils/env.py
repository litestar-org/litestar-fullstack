from __future__ import annotations

import json
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final, TypeVar, cast, get_args, get_origin, overload

if TYPE_CHECKING:
    from collections.abc import Callable

BASE_DIR: Final[Path] = Path(__file__).parent.parent
TRUE_VALUES: Final[frozenset[str]] = frozenset({"True", "true", "1", "yes", "YES", "Y", "y", "T", "t"})

T = TypeVar("T")
ParseTypes = bool | int | str | list[str] | Path | list[Path]


class UnsetType:
    """Placeholder for an Unset type.

    This helps differentiate None from the default
    """


_UNSET = UnsetType()


@overload
def get_env(key: str, default: bool, type_hint: UnsetType = _UNSET) -> Callable[[], bool]: ...


@overload
def get_env(key: str, default: int, type_hint: UnsetType = _UNSET) -> Callable[[], int]: ...


@overload
def get_env(key: str, default: str, type_hint: UnsetType = _UNSET) -> Callable[[], str]: ...


@overload
def get_env(key: str, default: Path, type_hint: UnsetType = _UNSET) -> Callable[[], Path]: ...


@overload
def get_env(key: str, default: list[Path], type_hint: UnsetType = _UNSET) -> Callable[[], list[Path]]: ...


@overload
def get_env(key: str, default: list[str], type_hint: UnsetType = _UNSET) -> Callable[[], list[str]]: ...


@overload
def get_env(key: str, default: None, type_hint: UnsetType = _UNSET) -> Callable[[], None]: ...


@overload
def get_env(key: str, default: ParseTypes | None, type_hint: type[T]) -> Callable[[], T]: ...


def get_env(
    key: str, default: ParseTypes | None, type_hint: type[T] | UnsetType = _UNSET
) -> Callable[[], ParseTypes | T | None]:
    return lambda: get_config_val(key=key, default=default, type_hint=type_hint)


@overload
def get_config_val(key: str, default: bool, type_hint: UnsetType = _UNSET) -> bool: ...


@overload
def get_config_val(key: str, default: int, type_hint: UnsetType = _UNSET) -> int: ...


@overload
def get_config_val(key: str, default: str, type_hint: UnsetType = _UNSET) -> str: ...


@overload
def get_config_val(key: str, default: Path, type_hint: UnsetType = _UNSET) -> Path: ...


@overload
def get_config_val(key: str, default: list[Path], type_hint: UnsetType = _UNSET) -> list[Path]: ...


@overload
def get_config_val(key: str, default: list[str], type_hint: UnsetType = _UNSET) -> list[str]: ...


@overload
def get_config_val(key: str, default: None, type_hint: UnsetType = _UNSET) -> None: ...


@overload
def get_config_val(key: str, default: ParseTypes | None, type_hint: type[T]) -> T: ...


def get_config_val(  # noqa: C901, PLR0911, PLR0915
    key: str, default: ParseTypes | None, type_hint: type[T] | UnsetType = _UNSET
) -> ParseTypes | T | None:
    """Parse environment variables, prioritizing explicit type hint over default's type.

    Args:
        key: Environment variable key
        default: Default value if key not found in environment
        type_hint: Optional type hint to use instead of inferring from `default`

    Raises:
        RuntimeError: Raised when the configuration value cannot be parsed.
        ValueError: Raised when the configuration value cannot be parsed.

    Returns:
        Parsed value of the specified type

    Note:
        If the default is an empty list and no type hint is provided, the function will return list[str] (not list[Path]).
        To get list[Path] in this case, provide a type hint (e.g., type_hint=list[Path]).
    """
    str_value = os.getenv(key)
    if str_value is None:
        return default
    value: str = str_value

    final_type: type | None = None
    item_constructor: Callable[[str], Any] | None = None
    parse_as_list = False

    if type_hint != _UNSET and isinstance(type_hint, type):
        final_type = type_hint
        origin = get_origin(type_hint)
        args = get_args(type_hint)

        # Direct check using string representation - more reliable than typing introspection
        if "list[" in str(type_hint) and "Path" in str(type_hint):
            parse_as_list = True
            item_constructor = Path  # Just use Path directly

        elif origin is list and args:
            parse_as_list = True
            item_type_arg = args[0]
            if item_type_arg is str:
                item_constructor = str
            elif isinstance(item_type_arg, type) and issubclass(item_type_arg, Path):
                item_constructor = item_type_arg
            else:
                msg = f"Unsupported item type '{item_type_arg}' in list type hint for key '{key}'"
                raise ValueError(msg)
    # If type_hint is list[Path] but not caught above, catch it here
    elif type_hint != _UNSET and str(type_hint) == "list[pathlib._local.Path]":
        parse_as_list = True
        item_constructor = Path
    elif default is not None:
        final_type = type(default)
        if isinstance(default, Path):
            # If default is a Path, always return Path(value)
            return Path(value)
        if isinstance(default, list):
            parse_as_list = True
            # If the default is a non-empty list and all elements are Path, use Path
            if default and all(isinstance(x, Path) for x in default):
                item_constructor = Path
            elif default and all(isinstance(x, str) for x in default):
                item_constructor = str
            else:
                # If the default is an empty list, default to str
                item_constructor = str

    if parse_as_list and not item_constructor:
        msg = f"Internal error: List parsing requested for key '{key}' but no item constructor determined."
        raise RuntimeError(msg)

    try:
        if parse_as_list and item_constructor:
            if item_constructor is Path:
                return _parse_list(key, value, item_constructor)
            return cast("list[str]", _parse_list(key, value, item_constructor))
        if final_type is str:
            return value
        if final_type is int:
            return int(value)
        if final_type is bool:
            return value in TRUE_VALUES
        if final_type is Path:
            return Path(value)
        if final_type is None or final_type is type(None):
            return value
        if type_hint != _UNSET and final_type is type_hint:
            return cast("T", final_type(value))  # pyright: ignore
    except (ValueError, TypeError, RuntimeError) as e:
        type_name = final_type.__name__ if final_type else "unknown"
        msg = f"Could not convert value '{value}' for key '{key}' to type {type_name}. Error: {e}"
        raise ValueError(msg) from e
    return value


def _parse_list(key: str, value: str, item_constructor: Callable[[str], T]) -> list[T]:
    if value.startswith("["):
        if not value.endswith("]"):
            msg = f"{key} is not a valid list representation."
            raise ValueError(msg)
        try:
            parsed_json: Any = json.loads(value)
            if not isinstance(parsed_json, list):
                msg = f"{key} is not a valid list representation."
                raise ValueError(msg)  # noqa: TRY004, TRY301
            constructed_list: list[T] = []
            for item in parsed_json:  # pyright: ignore
                item_str: str = str(item)  # pyright: ignore
                try:
                    constructed_list.append(item_constructor(item_str))
                except (ValueError, TypeError) as item_e:
                    constructor_name = getattr(item_constructor, "__name__", repr(item_constructor))
                    msg = f"Error converting item '{item_str}' (from JSON list) for key '{key}' using {constructor_name}: {item_e}"
                    raise ValueError(msg) from item_e

        except (json.JSONDecodeError, ValueError) as e:
            msg = f"{key} is not a valid list representation."
            raise ValueError(msg) from e
        return constructed_list
    items = value.split(",")
    constructed_list = []
    try:
        for item in items:
            constructed_list.append(item_constructor(item.strip()))
    except (ValueError, TypeError) as item_e:
        constructor_name = getattr(item_constructor, "__name__", repr(item_constructor))
        msg = f"Error converting item in comma-separated list for key '{key}' using {constructor_name}: {item_e}"
        raise ValueError(msg) from item_e
    return constructed_list

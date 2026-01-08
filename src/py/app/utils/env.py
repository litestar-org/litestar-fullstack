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
ParseTypes = bool | int | str | list[str] | Path | list[Path] | dict[str, Any]


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


@overload
def get_env(key: str, default: dict[str, Any], type_hint: UnsetType = _UNSET) -> Callable[[], dict[str, Any]]: ...


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


@overload
def get_config_val(key: str, default: dict[str, Any], type_hint: UnsetType = _UNSET) -> dict[str, Any]: ...


def get_config_val(  # noqa: C901, PLR0911, PLR0915
    key: str, default: ParseTypes | None, type_hint: type[T] | UnsetType = _UNSET
) -> ParseTypes | T | None:
    """Parse environment variables, prioritizing explicit type hint over default's type.
    Now supports dict and TypedDict with both JSON and comma-separated formats.

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
    parse_as_dict = False

    if type_hint != _UNSET:
        origin = get_origin(type_hint)
        args = get_args(type_hint)
        # Handle parameterized generics like list[Path], list[str], dict[str, Any]
        if origin is list and args:
            parse_as_list = True
            item_type_arg = args[0]
            if item_type_arg is str:
                item_constructor = str
            elif isinstance(item_type_arg, type) and issubclass(item_type_arg, Path):
                item_constructor = item_type_arg
            else:
                msg = f"Unsupported item type '{item_type_arg}' in list type hint for key '{key}'"
                raise ValueError(msg)
        elif origin is dict or is_typed_dict(type_hint):
            parse_as_dict = True
        elif isinstance(type_hint, type):
            final_type = type_hint
    elif type_hint != _UNSET and str(type_hint) == "list[pathlib._local.Path]":
        parse_as_list = True
        item_constructor = Path
    elif default is not None:
        final_type = type(default)
        if isinstance(default, Path):
            return Path(value)
        if isinstance(default, list):
            parse_as_list = True
            if default and all(isinstance(x, Path) for x in default):
                item_constructor = Path
            elif default and all(isinstance(x, str) for x in default):
                item_constructor = str
            else:
                item_constructor = str
        if isinstance(default, dict):
            parse_as_dict = True

    if parse_as_list and not item_constructor:
        msg = f"Internal error: List parsing requested for key '{key}' but no item constructor determined."
        raise RuntimeError(msg)

    if parse_as_list and item_constructor:
        if item_constructor is Path:
            return _parse_list(key, value, item_constructor)
        return cast("list[str]", _parse_list(key, value, item_constructor))
    if parse_as_dict:
        return _parse_dict(key, value)
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
        return cast("T", final_type(value))

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
                try:
                    constructed_list.append(item_constructor(item))  # pyright: ignore
                except (ValueError, TypeError) as item_e:
                    constructor_name = getattr(item_constructor, "__name__", repr(item_constructor))
                    msg = f"Error converting item '{item}' (from JSON list) for key '{key}' using {constructor_name}: {item_e}"
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


def _parse_dict(key: str, value: str) -> dict[str, Any]:
    # Try JSON first
    if value.strip().startswith("{"):
        return _parse_dict_json(key, value)

    return _parse_dict_comma(key, value)


def _parse_dict_json(key: str, value: str, key_type: type = str) -> dict[str, Any]:
    try:
        parsed_json: dict[str, Any] | Any = json.loads(value)
    except json.JSONDecodeError as e:
        msg = f"{key} is not a valid dict representation."
        raise TypeError(msg) from e
    if not isinstance(parsed_json, dict):
        msg = f"{key} is not a valid dict representation."
        raise TypeError(msg)
    result: dict[str, Any] = {}
    for k, v in parsed_json.items():  # pyright: ignore
        try:
            # Treat all values as strings when parsing from env var
            result[key_type(k)] = str(v)  # pyright: ignore
        except Exception as e:
            msg = f"Error converting value for key '{k}' in dict for env var '{key}': {e}"
            raise TypeError(msg) from e
    return result


def _parse_dict_comma(
    key: str, value: str, key_type: type = str
) -> dict[str, Any]:  # Fallback: comma-separated key=val pairs
    result: dict[str, Any] = {}

    for item in value.split(","):
        if not item.strip():
            continue
        if "=" not in item:
            msg = f"{key} is not a valid dict representation (missing '=' in '{item}')."
            raise TypeError(msg)
        k, v = item.split("=", 1)
        k_cast = key_type(k.strip())
        try:
            # Value is already a string here
            result[k_cast] = v.strip()
        except Exception as e:
            msg = f"Error converting value for key '{k_cast}' in dict for env var '{key}': {e}"
            raise TypeError(msg) from e
    return result


def is_typed_dict(tp: Any) -> bool:
    try:
        return (
            isinstance(tp, type) and issubclass(tp, dict) and hasattr(tp, "__annotations__") and tp.__name__ != "dict"  # pyright: ignore
        )
    except Exception:  # noqa: BLE001
        return False

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final, Literal, TypeVar, cast, get_args, get_origin, overload

if TYPE_CHECKING:
    from collections.abc import Callable

BASE_DIR: Final[Path] = Path(__file__).parent.parent
TRUE_VALUES: Final[frozenset[str]] = frozenset({"True", "true", "1", "yes", "YES", "Y", "y", "T", "t"})

T = TypeVar("T")
ParseTypes = bool | int | float | str | list[str] | tuple[str, ...] | Path | list[Path] | dict[str, Any]


class UnsetType:
    """Sentinel type marking an omitted ``type_hint``, so that ``None`` stays a usable default."""


_UNSET = UnsetType()


@overload
def get_env(key: str, default: bool, type_hint: UnsetType = _UNSET) -> Callable[[], bool]: ...


@overload
def get_env(key: str, default: int, type_hint: UnsetType = _UNSET) -> Callable[[], int]: ...


@overload
def get_env(key: str, default: float, type_hint: UnsetType = _UNSET) -> Callable[[], float]: ...


@overload
def get_env(key: str, default: str, type_hint: UnsetType = _UNSET) -> Callable[[], str]: ...


@overload
def get_env(key: str, default: Path, type_hint: UnsetType = _UNSET) -> Callable[[], Path]: ...


@overload
def get_env(key: str, default: list[Path], type_hint: UnsetType = _UNSET) -> Callable[[], list[Path]]: ...


@overload
def get_env(key: str, default: list[str], type_hint: UnsetType = _UNSET) -> Callable[[], list[str]]: ...


@overload
def get_env(key: str, default: tuple[str, ...], type_hint: UnsetType = _UNSET) -> Callable[[], tuple[str, ...]]: ...


@overload
def get_env(key: str, default: None, type_hint: UnsetType = _UNSET) -> Callable[[], None]: ...


@overload
def get_env(key: str, default: None, type_hint: type[T]) -> Callable[[], T | None]: ...


@overload
def get_env(key: str, default: ParseTypes, type_hint: type[T]) -> Callable[[], T]: ...


@overload
def get_env(key: str, default: dict[str, Any], type_hint: UnsetType = _UNSET) -> Callable[[], dict[str, Any]]: ...


def get_env(
    key: str, default: ParseTypes | None, type_hint: type[T] | UnsetType = _UNSET
) -> Callable[[], ParseTypes | T | None]:
    """Build a zero-argument reader of ``key`` for use as a dataclass ``default_factory``.

    Returns:
        Callable that parses the environment variable with :func:`get_config_val` each time it is called.
    """
    return lambda: get_config_val(key=key, default=default, type_hint=type_hint)


@overload
def get_config_val(key: str, default: bool, type_hint: UnsetType = _UNSET) -> bool: ...


@overload
def get_config_val(key: str, default: int, type_hint: UnsetType = _UNSET) -> int: ...


@overload
def get_config_val(key: str, default: float, type_hint: UnsetType = _UNSET) -> float: ...


@overload
def get_config_val(key: str, default: str, type_hint: UnsetType = _UNSET) -> str: ...


@overload
def get_config_val(key: str, default: Path, type_hint: UnsetType = _UNSET) -> Path: ...


@overload
def get_config_val(key: str, default: list[Path], type_hint: UnsetType = _UNSET) -> list[Path]: ...


@overload
def get_config_val(key: str, default: list[str], type_hint: UnsetType = _UNSET) -> list[str]: ...


@overload
def get_config_val(key: str, default: tuple[str, ...], type_hint: UnsetType = _UNSET) -> tuple[str, ...]: ...


@overload
def get_config_val(key: str, default: None, type_hint: UnsetType = _UNSET) -> None: ...


@overload
def get_config_val(key: str, default: None, type_hint: type[T]) -> T | None: ...


@overload
def get_config_val(key: str, default: ParseTypes, type_hint: type[T]) -> T: ...


@overload
def get_config_val(key: str, default: dict[str, Any], type_hint: UnsetType = _UNSET) -> dict[str, Any]: ...


def get_config_val(
    key: str, default: ParseTypes | None, type_hint: type[T] | UnsetType = _UNSET
) -> ParseTypes | T | None:
    """Parse an environment variable as ``type_hint``, or as the type of ``default`` when no hint is given.

    Lists and tuples accept a JSON array or a comma-separated string, and drop empty items. A list of
    ``Literal`` strings accepts only those strings. Dicts and TypedDicts accept a JSON object or
    comma-separated ``key=value`` pairs, and their values are always returned as strings. An empty list
    default parses as ``list[str]``; pass ``type_hint=list[Path]`` to get paths instead.

    An empty value counts as unset for numbers. A ``None`` default makes the hinted type optional: an
    empty value, or a list with no items, yields ``None``.

    A value that cannot be parsed raises ``ValueError``, or ``TypeError`` for a malformed dict.

    Args:
        key: Environment variable key
        default: Default value if key not found in environment
        type_hint: Optional type hint to use instead of inferring from `default`

    Returns:
        Parsed value of the specified type, or ``default`` when the variable is not set.
    """
    value = os.getenv(key)
    if value is None:
        return default
    is_optional = default is None and not isinstance(type_hint, UnsetType)
    parse_type = _type_of_default(default) if isinstance(type_hint, UnsetType) else type_hint
    if not value and (is_optional or parse_type in {int, float}):
        return default
    parsed = _parse_as_type(key, value, parse_type)
    if is_optional and parsed in ([], ()):
        return None
    return cast("ParseTypes | T", parsed)


def is_typed_dict(type_hint: Any) -> bool:
    """Return whether ``type_hint`` is a ``TypedDict`` class rather than plain ``dict``."""
    try:
        return (
            isinstance(type_hint, type)
            and hasattr(type_hint, "__annotations__")
            and issubclass(type_hint, dict)
            and type_hint.__name__ != "dict"
        )
    except Exception:  # noqa: BLE001
        return False


def _type_of_default(default: ParseTypes | None) -> object:
    if isinstance(default, list):
        return list[Path] if default and all(isinstance(item, Path) for item in default) else list[str]
    if isinstance(default, tuple):
        return tuple[str, ...]
    if isinstance(default, dict):
        return dict[str, str]
    if isinstance(default, Path):
        return Path
    return type(default) if type(default) in {bool, int, float} else str


def _parse_as_type(key: str, value: str, parse_type: object) -> object:
    origin = get_origin(parse_type)
    item_types = get_args(parse_type)
    if origin in {list, tuple} and item_types:
        items = _parse_items(key, value, item_types[0])
        return tuple(items) if origin is tuple else items
    if origin is dict or is_typed_dict(parse_type):
        return _parse_dict(key, value)
    if parse_type is bool:
        return value in TRUE_VALUES
    if isinstance(parse_type, type) and parse_type is not type(None):
        return parse_type(value)
    return value


def _parse_items(key: str, value: str, item_type: Any) -> list[Any]:
    if get_origin(item_type) is Literal:
        items = _parse_list(key, value, str)
        unknown = [item for item in items if item not in get_args(item_type)]
        if unknown:
            msg = f"Unsupported items {unknown} for key '{key}'; expected any of {list(get_args(item_type))}"
            raise ValueError(msg)
        return items
    if item_type is not str and not (isinstance(item_type, type) and issubclass(item_type, Path)):
        msg = f"Unsupported item type '{item_type}' in list type hint for key '{key}'"
        raise ValueError(msg)
    return _parse_list(key, value, item_type)


def _parse_list(key: str, value: str, item_constructor: Callable[[str], T]) -> list[T]:
    if not value.startswith("["):
        try:
            return [item_constructor(item) for item in map(str.strip, value.split(",")) if item]
        except (ValueError, TypeError) as exc:
            constructor_name = getattr(item_constructor, "__name__", repr(item_constructor))
            msg = f"Error converting item in comma-separated list for key '{key}' using {constructor_name}: {exc}"
            raise ValueError(msg) from exc
    msg = f"{key} is not a valid list representation."
    if not value.endswith("]"):
        raise ValueError(msg)
    try:
        items: list[Any] = json.loads(value)
        return [item_constructor(item) for item in items if item != ""]
    except (ValueError, TypeError) as exc:
        raise ValueError(msg) from exc


def _parse_dict(key: str, value: str) -> dict[str, str]:
    if value.strip().startswith("{"):
        return _parse_dict_json(key, value)
    return _parse_dict_comma(key, value)


def _parse_dict_json(key: str, value: str) -> dict[str, str]:
    try:
        entries: dict[str, Any] = json.loads(value)
    except json.JSONDecodeError as exc:
        msg = f"{key} is not a valid dict representation."
        raise TypeError(msg) from exc
    return {name: str(entry) for name, entry in entries.items()}


def _parse_dict_comma(key: str, value: str) -> dict[str, str]:
    entries: dict[str, str] = {}
    for pair in value.split(","):
        if not pair.strip():
            continue
        if "=" not in pair:
            msg = f"{key} is not a valid dict representation (missing '=' in '{pair}')."
            raise TypeError(msg)
        name, entry = pair.split("=", 1)
        entries[name.strip()] = entry.strip()
    return entries

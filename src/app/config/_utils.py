from __future__ import annotations

import json
import os
from pathlib import Path
from typing import TYPE_CHECKING, Final, TypeVar, cast, overload

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


def get_config_val(  # noqa: C901, PLR0912, PLR0911
    key: str, default: ParseTypes | None, type_hint: type[T] | UnsetType = _UNSET
) -> ParseTypes | T | None:
    """Parse environment variables.

    Args:
        key: Environment variable key
        default: Default value if key not found in environment
        type_hint: Optional type hint to use instead of inferring from `default`

    Raises:
        ValueError: Raised when the configuration value cannot be parsed.

    Returns:
        Parsed value of the specified type
    """
    str_value = os.getenv(key)
    if str_value is None:
        if type_hint != _UNSET:
            return cast("T", default)
        return default
    value: str = str_value
    if type(default) is bool:
        bool_value = value in TRUE_VALUES
        if type_hint != _UNSET:
            return cast("T", bool_value)
        return bool_value
    if type(default) is int:
        int_value = int(value)
        if type_hint != _UNSET:
            return cast("T", int_value)
        return int_value
    if type(default) is Path:
        path_value = Path(value)
        if type_hint != _UNSET:
            return cast("T", path_value)
        return path_value
    if type(default) is list[Path]:
        if value.startswith("[") and value.endswith("]"):
            try:
                path_list = [Path(s) for s in json.loads(value)]
                if type_hint != _UNSET:
                    return cast("T", path_list)
            except (SyntaxError, ValueError) as e:
                msg = f"{key} is not a valid list representation."
                raise ValueError(msg) from e
            else:
                return value
        path_list = [Path(host.strip()) for host in value.split(",")]
        if type_hint != _UNSET:
            return cast("T", path_list)
        return path_list
    if type(default) is list[str]:
        if value.startswith("[") and value.endswith("]"):
            try:
                str_list = cast("list[str]", json.loads(value))
                if type_hint != _UNSET:
                    return cast("T", str_list)
            except (SyntaxError, ValueError) as e:
                msg = f"{key} is not a valid list representation."
                raise ValueError(msg) from e
            else:
                return value
        str_list = [host.strip() for host in value.split(",")]
        if type_hint != _UNSET:
            return cast("T", str_list)
        return str_list
    if type_hint != _UNSET:
        return cast("T", value)
    return value

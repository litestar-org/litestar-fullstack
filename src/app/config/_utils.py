from __future__ import annotations

import json
import os
from pathlib import Path
from typing import TYPE_CHECKING, Final, TypeVar, cast, overload

if TYPE_CHECKING:
    from collections.abc import Callable

BASE_DIR: Final[Path] = Path(__file__).parent.parent
TRUE_VALUES: Final[frozenset[str]] = frozenset({"True", "true", "1", "yes", "Y", "T"})

T = TypeVar("T")
ParseTypes = bool | int | str | list[str]


@overload
def get_env(key: str, default: bool) -> Callable[[], bool]: ...


@overload
def get_env(key: str, default: int) -> Callable[[], int]: ...


@overload
def get_env(key: str, default: str) -> Callable[[], str]: ...


@overload
def get_env(key: str, default: list[str]) -> Callable[[], list[str]]: ...


def get_env(key: str, default: ParseTypes) -> Callable[[], ParseTypes]:
    return lambda: get_config_val(key, default)


@overload
def get_config_val(key: str, default: bool) -> bool: ...


@overload
def get_config_val(key: str, default: int) -> int: ...


@overload
def get_config_val(key: str, default: str) -> str: ...


@overload
def get_config_val(key: str, default: list[str]) -> list[str]: ...


def get_config_val(
    key: str,
    default: ParseTypes,
) -> ParseTypes:
    """Parse environment variables.

    Args:
        key: Environment variable key
        default: Default value if key not found in environment

    Returns:
        Parsed value of the specified type
    """
    value = os.getenv(key)
    if value is None:
        return default
    if type(default) is bool:
        return value in TRUE_VALUES
    if type(default) is int:
        return int(value)
    if type(default) is list[str]:
        if value.startswith("[") and value.endswith("]"):
            try:
                return cast("list[str]", json.loads(value))
            except (SyntaxError, ValueError) as e:
                msg = f"{key} is not a valid list representation."
                raise ValueError(msg) from e
        return [host.strip() for host in value.split(",")]
    return value

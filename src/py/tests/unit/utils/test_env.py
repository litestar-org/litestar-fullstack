"""Unit tests for environment variable parsing behind settings defaults."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import pytest

from app.utils.env import get_config_val, get_env

Channel = Literal["email", "sms", "push"]


def test_unset_variable_returns_the_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SAMPLE", raising=False)

    assert get_config_val("SAMPLE", 0.25) == 0.25
    assert get_config_val("SAMPLE", ("a", "b")) == ("a", "b")
    assert get_config_val("SAMPLE", None, int) is None


@pytest.mark.parametrize(
    ("value", "default", "expected"),
    [
        ("0.5", 0.25, 0.5),
        ("2", 0.25, 2.0),
        ("", 0.25, 0.25),
        ("7", 5, 7),
        ("", 5, 5),
    ],
)
def test_numbers_parse_and_an_empty_value_counts_as_unset(
    monkeypatch: pytest.MonkeyPatch,
    value: str,
    default: float,
    expected: float,
) -> None:
    monkeypatch.setenv("SAMPLE", value)

    parsed = get_config_val("SAMPLE", default)

    assert parsed == expected
    assert type(parsed) is type(default)


def test_malformed_number_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SAMPLE", "fast")

    with pytest.raises(ValueError, match="could not convert string to float"):
        get_config_val("SAMPLE", 0.25)


@pytest.mark.parametrize(
    ("value", "type_hint", "expected"),
    [
        ("60", int, 60),
        ("", int, None),
        ("true", bool, True),
        ("0", bool, False),
        ("", bool, None),
        ("a, b", list[str], ["a", "b"]),
        ('["a", "b"]', list[str], ["a", "b"]),
        ("", list[str], None),
        (" ", list[str], None),
        (",", list[str], None),
        ('[""]', list[str], None),
    ],
)
def test_none_default_makes_the_hinted_type_optional(
    monkeypatch: pytest.MonkeyPatch,
    value: str,
    type_hint: type,
    expected: object,
) -> None:
    monkeypatch.setenv("SAMPLE", value)

    assert get_config_val("SAMPLE", None, type_hint) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("emails,reports", ("emails", "reports")),
        (" emails , ,reports,", ("emails", "reports")),
        ('["emails", "reports"]', ("emails", "reports")),
        ("", ()),
    ],
)
def test_tuple_default_parses_a_tuple_of_names(
    monkeypatch: pytest.MonkeyPatch,
    value: str,
    expected: tuple[str, ...],
) -> None:
    monkeypatch.setenv("SAMPLE", value)

    assert get_config_val("SAMPLE", ("default",)) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("", []),
        (" ", []),
        ("10.0.0.1,,10.0.0.2,", ["10.0.0.1", "10.0.0.2"]),
        ('["10.0.0.1", ""]', ["10.0.0.1"]),
    ],
)
def test_lists_drop_empty_items(monkeypatch: pytest.MonkeyPatch, value: str, expected: list[str]) -> None:
    monkeypatch.setenv("SAMPLE", value)

    assert get_config_val("SAMPLE", ["127.0.0.1"]) == expected
    assert get_config_val("SAMPLE", [], list[str]) == expected


def test_list_of_paths_drops_empty_items(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SAMPLE", "/srv/a,,/srv/b")

    assert get_config_val("SAMPLE", [Path("/srv")]) == [Path("/srv/a"), Path("/srv/b")]


@pytest.mark.parametrize("value", ["email,push", '["email", "push"]'])
def test_list_of_literal_accepts_the_literal_values(monkeypatch: pytest.MonkeyPatch, value: str) -> None:
    monkeypatch.setenv("SAMPLE", value)

    assert get_config_val("SAMPLE", ["email"], list[Channel]) == ["email", "push"]


def test_list_of_literal_rejects_other_values(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SAMPLE", "email,fax")

    with pytest.raises(ValueError, match="fax"):
        get_config_val("SAMPLE", ["email"], list[Channel])


def test_get_env_reads_the_variable_each_time_it_is_called(monkeypatch: pytest.MonkeyPatch) -> None:
    read_poll_interval = get_env("SAMPLE", 0.25)
    monkeypatch.delenv("SAMPLE", raising=False)
    assert read_poll_interval() == 0.25

    monkeypatch.setenv("SAMPLE", "1.5")
    assert read_poll_interval() == 1.5

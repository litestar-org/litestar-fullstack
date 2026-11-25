"""Unit tests for the constrained field types shared by API schemas."""

from __future__ import annotations

from typing import Any

import msgspec
import pytest

from app.lib.schema import Email, Name, Phone, Username


@pytest.mark.parametrize(
    ("field_type", "value"),
    [
        (Email, "valid@example.com"),
        (Email, "First.Last+tag@Mail.Example.org"),
        (Email, f"{'a' * 64}@example.com"),
        (Name, "Zoë O'Brien-Smith Jr."),
        (Name, "山田 太郎"),
        (Name, "a" * 100),
        (Username, "octo_cat-9"),
        (Username, "abc"),
        (Username, "a" * 30),
        (Phone, "+1 (555) 123-4567"),
        (Phone, "5551234"),
    ],
)
def test_field_types_accept_well_formed_values(field_type: Any, value: str) -> None:
    assert msgspec.convert(value, field_type) == value


@pytest.mark.parametrize(
    ("field_type", "value"),
    [
        (Email, "invalid-email"),
        (Email, "spaced out@example.com"),
        (Email, f"{'a' * 65}@example.com"),
        (Email, f"user@{'d' * 250}.com"),
        (Name, ""),
        (Name, "   "),
        (Name, "a" * 101),
        (Name, "Robert <script>"),
        (Username, "ab"),
        (Username, "a" * 31),
        (Username, "-leading-hyphen"),
        (Username, "Uppercase"),
        (Phone, "555-123"),
        (Phone, "1" * 16),
        (Phone, "call me maybe"),
        (Phone, "+1 (555) 123-4567 ext"),
    ],
)
def test_field_types_reject_malformed_values(field_type: Any, value: str) -> None:
    with pytest.raises(msgspec.ValidationError):
        msgspec.convert(value, field_type)

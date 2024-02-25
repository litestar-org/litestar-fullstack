from pathlib import Path
from typing import Any

from litestar.serialization import decode_json

__all__ = ("open_fixture",)


def open_fixture(fixtures_path: Path, fixture_name: str) -> Any:
    fixture = Path(fixtures_path / f"{fixture_name}.json")
    if fixture.exists():
        with fixture.open(mode="r", encoding="utf-8") as f:
            f_data = f.read()
        return decode_json(f_data)
    msg = f"Could not find the '{fixture_name}' fixture in '{fixtures_path}'"
    raise FileNotFoundError(msg)

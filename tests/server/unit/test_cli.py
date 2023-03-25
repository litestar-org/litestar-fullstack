from collections.abc import Generator
from typing import Any

import pytest
from click.testing import CliRunner

from app.cli import app as cli_app


@pytest.fixture
def cli_runner() -> Generator[CliRunner, None, None]:
    yield CliRunner()


def test_manage_generate_random_key(cli_runner: Any) -> None:
    result = cli_runner.invoke(cli_app, ["manage", "generate-random-key"])
    assert result.exit_code == 0
    assert "KEY:" in result.output

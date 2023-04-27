from collections.abc import Generator
from typing import Any
from unittest.mock import MagicMock

import pytest
from click.testing import CliRunner

import app.cli


@pytest.fixture
def cli_runner() -> Generator[CliRunner, None, None]:
    yield CliRunner()


def test_run_server(cli_runner: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    run_server_subprocess = MagicMock()
    monkeypatch.setattr(app.cli, "run_server", run_server_subprocess)
    result = cli_runner.invoke(app.cli.app, ["run", "server"])
    assert result.exit_code == 0


def test_manage_generate_random_key(cli_runner: Any) -> None:
    result = cli_runner.invoke(app.cli.app, ["manage", "generate-random-key"])
    assert result.exit_code == 0
    assert "KEY:" in result.output

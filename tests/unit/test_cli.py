from typing import Any
from unittest.mock import MagicMock

import pytest
from click.testing import CliRunner


@pytest.fixture()
def cli_runner() -> CliRunner:
    return CliRunner()


def test_run_server(cli_runner: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    import app.cli

    run_server_subprocess = MagicMock()
    monkeypatch.setattr(app.cli, "run_all_app", run_server_subprocess)
    result = cli_runner.invoke(app.cli.run_all_app)
    assert result.exit_code == 0

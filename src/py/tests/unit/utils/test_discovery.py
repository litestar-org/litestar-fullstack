from typing import cast
from unittest.mock import MagicMock, patch

from app.utils.domain import _discovery as discovery


def test_discover_domain_schemas() -> None:
    mock_module = MagicMock()
    mock_module.__all__ = ["SchemaA", "SchemaB"]
    mock_module.SchemaA = "SchemaA_Obj"
    mock_module.SchemaB = "SchemaB_Obj"

    with (
        patch("app.utils.domain._discovery._iter_submodules", return_value=["pkg.sub"]),
        patch("importlib.import_module", return_value=mock_module) as mock_import,
    ):
        schemas = discovery.discover_domain_schemas(["pkg"])

        assert schemas == {"SchemaA": "SchemaA_Obj", "SchemaB": "SchemaB_Obj"}
        mock_import.assert_called_with("pkg.sub")


def test_discover_domain_services() -> None:
    mock_module = MagicMock()
    mock_module.__all__ = ["ServiceA"]
    mock_module.ServiceA = "ServiceA_Obj"

    with (
        patch("app.utils.domain._discovery._iter_submodules", return_value=["pkg.sub"]),
        patch("importlib.import_module", return_value=mock_module),
    ):
        services = discovery.discover_domain_services(["pkg"])

        assert services == {"ServiceA": "ServiceA_Obj"}


def test_discover_domain_signals() -> None:
    mock_module = MagicMock()
    mock_module.__all__ = ["SignalA"]
    mock_module.SignalA = "SignalA_Obj"

    with (
        patch("app.utils.domain._discovery._iter_submodules", return_value=["pkg.sub"]),
        patch("importlib.import_module", return_value=mock_module),
    ):
        signals = discovery.discover_domain_signals(["pkg"])

        assert cast("list[str]", signals) == ["SignalA_Obj"]


def test_discover_domain_repositories() -> None:
    mock_module = MagicMock()
    mock_module.__all__ = ["RepoA"]
    mock_module.RepoA = "RepoA_Obj"

    with (
        patch("app.utils.domain._discovery._iter_submodules", return_value=["pkg.sub"]),
        patch("importlib.import_module", return_value=mock_module),
    ):
        repos = discovery.discover_domain_repositories(["pkg"])

        assert repos == {"RepoA": "RepoA_Obj"}

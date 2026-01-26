from typing import Any

from advanced_alchemy.extensions.litestar import SQLAlchemyDTOConfig
from litestar.dto.config import DTOConfig

from app.utils.dto import config


def test_config_dataclass_default() -> None:
    """Test default dataclass configuration."""
    cfg = config(backend="dataclass")
    assert isinstance(cfg, DTOConfig)
    assert cfg.rename_strategy == "camel"
    assert cfg.max_nested_depth == 2


def test_config_sqlalchemy_default() -> None:
    """Test default sqlalchemy configuration."""
    cfg = config(backend="sqlalchemy")
    assert isinstance(cfg, SQLAlchemyDTOConfig)
    assert cfg.rename_strategy == "camel"
    assert cfg.max_nested_depth == 2


def test_config_with_custom_values() -> None:
    """Test configuration with custom values."""
    include = {"field1", "field2"}
    rename_fields: dict[str, Any] = {"field1": "field_one"}

    cfg = config(
        backend="dataclass",
        include=include,
        rename_fields=rename_fields,
        rename_strategy="camel",
        max_nested_depth=5,
        partial=True,
    )

    assert cfg.include == include
    assert cfg.rename_fields == rename_fields
    assert cfg.rename_strategy == "camel"
    assert cfg.max_nested_depth == 5
    assert cfg.partial is True


def test_config_with_exclude() -> None:
    """Test configuration with exclude."""
    exclude = {"field3"}
    cfg = config(backend="dataclass", exclude=exclude)
    assert cfg.exclude == exclude


def test_config_sqlalchemy_with_custom_values() -> None:
    """Test sqlalchemy configuration with custom values."""
    cfg = config(backend="sqlalchemy", max_nested_depth=3, partial=True)
    assert isinstance(cfg, SQLAlchemyDTOConfig)
    assert cfg.max_nested_depth == 3
    assert cfg.partial is True

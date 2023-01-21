from starlite.config.compression import CompressionConfig

from app.utils.module_loader import import_string


def test_import_string() -> None:
    cls = import_string("starlite.config.compression.CompressionConfig")
    assert type(cls) == type(CompressionConfig)


def test_import_string_missing() -> None:
    try:
        cls = import_string("starlite.config.compression.CompressionConfig")
    except ImportError:
        cls = None
    assert cls is None

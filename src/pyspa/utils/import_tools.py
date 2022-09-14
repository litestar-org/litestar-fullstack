"""
All configuration is via environment variables.

Take not of the environment variable prefixes required for each settings class, except
[`AppSettings`][starlite_bedrock.config.AppSettings].
"""
import pkgutil
from functools import lru_cache
from importlib.machinery import SourceFileLoader
from pathlib import Path


@lru_cache
def module_to_os_path(dotted_path: str = "pyspa") -> Path:
    """
    Returns the path to the base directory of the project or the module specified by `dotted_path`.

    Ensures that pkgutil returns a valid source file loader.
    """
    src = pkgutil.get_loader(dotted_path)
    if not isinstance(src, SourceFileLoader):
        raise ValueError(f"Couldn't find the path for {dotted_path}")
    return Path(str(src.path).removesuffix("/__init__.py"))

"""Compression configuration for the application."""
from __future__ import annotations

from starlite.config.compression import CompressionConfig

config = CompressionConfig(backend="gzip")
"""Default compression config."""

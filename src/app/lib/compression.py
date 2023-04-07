"""Compression configuration for the application."""
from __future__ import annotations

from litestar.config.compression import CompressionConfig

config = CompressionConfig(backend="gzip")
"""Default compression config."""

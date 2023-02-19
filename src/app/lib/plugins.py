from starlite_saqlalchemy import ConfigureApp as SAQLAlchemyPlugin
from starlite_saqlalchemy import PluginConfig as SAQLAlchemyPluginConfig

from . import settings

__all__ = ["saqlalchemy"]

saqlalchemy = SAQLAlchemyPlugin(
    config=SAQLAlchemyPluginConfig(
        do_after_exception=True,
        do_cache=True,
        do_sentry=False,
        do_compression=True,
        do_logging=True,
        do_exception_handlers=True,
        do_worker=bool(settings.worker.INIT_METHOD == "integrated"),
    )
)
"""Configures `starlite-saqlalchemy` plugin.

Setting INIT_METHOD to `standalone` will start the Background Worker
process in a separate process instead of with each HTTP worker.
"""

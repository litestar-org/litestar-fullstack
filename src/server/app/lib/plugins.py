from starlite_saqlalchemy import ConfigureApp as SAQLAlchemyPlugin
from starlite_saqlalchemy import PluginConfig as SAQLAlchemyPluginConfig

saqlalchemy = SAQLAlchemyPlugin(
    config=SAQLAlchemyPluginConfig(
        do_after_exception=True, do_cache=True, do_sentry=False, do_compression=True, do_logging=True
    )
)

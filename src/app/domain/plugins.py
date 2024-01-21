from litestar.plugins.sqlalchemy import SQLAlchemyPlugin
from litestar.plugins.structlog import StructlogPlugin
from litestar_granian import GranianPlugin
from litestar_saq import SAQPlugin
from litestar_vite import VitePlugin

from . import config

structlog = StructlogPlugin(config=config.log)
vite = VitePlugin(config=config.vite)
saq = SAQPlugin(config=config.saq)
alchemy = SQLAlchemyPlugin(config=config.alchemy)
granian = GranianPlugin()

from functools import cache

from advanced_alchemy.extensions.litestar import SQLAlchemyPlugin
from litestar.plugins.problem_details import ProblemDetailsPlugin
from litestar.plugins.structlog import StructlogPlugin
from litestar_email import EmailPlugin
from litestar_granian import GranianPlugin
from litestar_saq import SAQPlugin
from litestar_vite import VitePlugin

from app import config
from app.utils.oauth import OAuth2ProviderPlugin

structlog = StructlogPlugin(config=config.log)
vite = VitePlugin(config=config.vite)
alchemy = SQLAlchemyPlugin(config=config.alchemy)
granian = GranianPlugin()
problem_details = ProblemDetailsPlugin(config=config.problem_details)
oauth2_provider = OAuth2ProviderPlugin()
email = EmailPlugin(config=config.email)


@cache
def get_saq_plugin() -> SAQPlugin:
    """Get SAQ plugin lazily to avoid Redis connection during build."""
    return SAQPlugin(config=config.get_saq_config())

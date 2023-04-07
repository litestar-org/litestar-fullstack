from litestar.config.csrf import CSRFConfig

from app.lib import settings

config = CSRFConfig(
    secret=settings.app.SECRET_KEY.get_secret_value().decode(),
    cookie_httponly=True,
    cookie_secure=settings.app.CSRF_COOKIE_SECURE,
    cookie_name=settings.app.CSRF_COOKIE_NAME,
)
"""Default csrf config."""

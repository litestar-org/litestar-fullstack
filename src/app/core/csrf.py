from starlite.config.csrf import CSRFConfig

from app.config import settings

config = CSRFConfig(
    secret=settings.app.SECRET_KEY.get_secret_value(),
    cookie_httponly=True,
    cookie_secure=settings.app.CSRF_COOKIE_SECURE,
    cookie_name=settings.app.CSRF_COOKIE_NAME,
)
"""Default compression config"""

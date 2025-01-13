import pytest
from litestar.config.response_cache import default_cache_key_builder
from litestar.testing import RequestFactory

from app.server.core import ApplicationCore

pytestmark = pytest.mark.anyio


def test_cache_key_builder(monkeypatch: "pytest.MonkeyPatch") -> None:
    monkeypatch.setattr(ApplicationCore, "app_slug", "the-slug")
    request = RequestFactory().get("/test")
    default_cache_key = default_cache_key_builder(request)
    assert ApplicationCore()._cache_key_builder(request) == f"the-slug:{default_cache_key}"

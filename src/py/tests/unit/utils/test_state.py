from unittest.mock import MagicMock, patch

from app.utils.domain._state import DiscoveryCache, DiscoveryState


def test_discovery_cache_basic() -> None:
    cache = DiscoveryCache()
    assert cache.get() is None
    assert cache.is_cached(["pkg1"]) is False

    mock_ctrl = MagicMock()
    cache.set([mock_ctrl], ["pkg1"])  # type: ignore[arg-type]

    assert cache.get() == [mock_ctrl]
    assert cache.is_cached(["pkg1"]) is True
    assert cache.is_cached(["pkg2"]) is False

    cache.clear()
    assert cache.get() is None
    assert cache.is_cached(["pkg1"]) is False


def test_discovery_state_reset() -> None:
    DiscoveryState.controller_count = 10
    DiscoveryState.reset()
    assert DiscoveryState.controller_count == 0
    assert DiscoveryState.controllers_by_domain == {}


def test_discovery_state_log() -> None:
    DiscoveryState.reset()
    DiscoveryState.controller_count = 5
    DiscoveryState.service_count = 3
    DiscoveryState.controllers_by_domain = {"domain1": ["Ctrl1"]}

    with patch("app.utils.domain._state.logger") as mock_logger:
        DiscoveryState.log_discovery_results()
        mock_logger.info.assert_called_once()
        assert DiscoveryState.logged_controllers is True

        # Second call should not log again
        mock_logger.reset_mock()
        DiscoveryState.log_discovery_results()
        mock_logger.info.assert_not_called()

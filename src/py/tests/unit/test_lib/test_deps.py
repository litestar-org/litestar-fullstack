from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Assuming 'app.lib.deps' is the module containing get_task_queue
from app.lib import deps


@pytest.mark.asyncio
async def test_get_task_queue() -> None:
    """Test that get_task_queue retrieves and connects the correct queue."""
    # Mock the queue object that get_queue should return
    mock_queue = AsyncMock()
    mock_queue.connect = AsyncMock()  # Mock the connect method

    # Mock the saq plugin object
    mock_saq_plugin = MagicMock()
    mock_saq_plugin.get_queue = MagicMock(return_value=mock_queue)

    # Patch the saq plugin directly in the plugins module
    with patch("app.server.plugins.saq", mock_saq_plugin):
        # Call the function under test
        returned_queue = await deps.get_task_queue()

        # Assertions
        mock_saq_plugin.get_queue.assert_called_once_with("background-tasks")
        mock_queue.connect.assert_awaited_once()
        assert returned_queue is mock_queue

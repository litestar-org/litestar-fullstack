from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from saq import Job, Queue, Status

from app.lib import worker

if TYPE_CHECKING:
    from saq.types import Context


@pytest.fixture()
def mock_queue() -> MagicMock:
    """Fixture for a mock SAQ Queue."""
    queue = MagicMock(spec=Queue)
    queue.name = "test_queue"
    return queue


@pytest.fixture()
def mock_worker(mock_queue: MagicMock) -> MagicMock:
    """Fixture for a mock SAQ Worker."""
    saq_worker = MagicMock()
    saq_worker.queue = mock_queue
    return saq_worker


@pytest.fixture()
def mock_job(mock_queue: MagicMock) -> MagicMock:  # Return MagicMock to allow attribute mocking
    """Fixture for a mock SAQ Job."""
    # Mock the Job object instead of creating a real one
    job = MagicMock(spec=Job)
    job.function = "test_function"
    job.kwargs = {"arg1": "value1"}
    job.queue = mock_queue
    job.key = "test_key"
    job.scheduled = 0
    job.attempts = 1
    job.completed = 0
    job.queued = 0
    job.started = 0
    job.result = None
    job.error = None
    job.status = Status.QUEUED
    job.id = "test_job_id"  # Mock the id attribute
    # Mock methods if needed, e.g., job.update = AsyncMock()
    return job


async def test_on_startup(mock_worker: MagicMock) -> None:
    """Test on_startup logs correctly."""
    ctx: Context = {"worker": mock_worker}
    with patch("app.lib.worker.logger", new_callable=AsyncMock) as mock_logger:
        await worker.on_startup(ctx)
        mock_logger.ainfo.assert_called_once_with(
            "🚀 Launching background workers for queue", queue=mock_worker.queue.name
        )


async def test_on_shutdown(mock_worker: MagicMock) -> None:
    """Test on_shutdown logs correctly."""
    ctx: Context = {"worker": mock_worker}
    with patch("app.lib.worker.logger", new_callable=AsyncMock) as mock_logger:
        await worker.on_shutdown(ctx)
        mock_logger.ainfo.assert_called_once_with("Stopping background workers for queue", queue=mock_worker.queue.name)


async def test_before_process(mock_job: Job, mock_worker: MagicMock) -> None:
    """Test before_process clears contextvars and logs."""
    ctx: Context = {"job": mock_job, "worker": mock_worker}
    with (
        patch("app.lib.worker.logger", new_callable=AsyncMock) as mock_logger,
        patch("app.lib.worker.structlog.contextvars.clear_contextvars") as mock_clear,
    ):
        await worker.before_process(ctx)
        mock_clear.assert_called_once()
        mock_logger.ainfo.assert_called_once_with(
            f"starting job {mock_job.function} with id {mock_job.id}", task=mock_job.function
        )


@pytest.mark.parametrize(
    ("status", "log_method"),
    [
        (Status.COMPLETE, "ainfo"),
        (Status.FAILED, "aerror"),
        (Status.ABORTED, "awarning"),
        (Status.QUEUED, "ainfo"),  # Changed DEFERRED to QUEUED as an example 'other' status
    ],
)
async def test_after_process(mock_job: Job, mock_worker: MagicMock, status: Status, log_method: str) -> None:
    """Test after_process logs correctly for different job statuses."""
    mock_job.status = status
    mock_job.started = 1000  # Example timestamp
    mock_job.queued = 500  # Example timestamp
    mock_job.completed = 2000  # Example timestamp with fixed spacing
    ctx: Context = {"job": mock_job, "worker": mock_worker}

    with (
        patch("app.lib.worker.logger", new_callable=AsyncMock) as mock_logger,
        patch("app.lib.worker.structlog.contextvars.clear_contextvars") as mock_clear,
        patch(
            "app.lib.worker.seconds",
            return_value=1.0,  # Mock duration calculation with fixed spacing
        ) as mock_seconds,
    ):
        await worker.after_process(ctx)

        log_ctx = {k: getattr(mock_job, k) for k in worker.LOGGED_JOB_FIELDS}
        log_ctx["pickup_time_ms"] = mock_job.started - mock_job.queued
        log_ctx["total_runtime_ms"] = mock_job.completed - mock_job.started
        log_ctx["total_time_ms"] = mock_job.completed - mock_job.queued

        log_call = getattr(mock_logger, log_method)
        assert log_call.call_count == 1
        call_args, call_kwargs = log_call.call_args
        assert call_kwargs == log_ctx  # Check logged context with fixed spacing

        # Check the message format based on status
        if status == Status.FAILED:
            assert call_args[0] == f"job {mock_job.function} with id '{mock_job.id}' failed after 1.0 seconds."
        elif status == Status.COMPLETE:
            assert call_args[0] == f"job {mock_job.function} with id '{mock_job.id}' completed after 1.0 seconds."
        elif status == Status.ABORTED:
            assert call_args[0] == f"job {mock_job.function} with id '{mock_job.id}' was aborted after 1.0 seconds"
        else:
            assert (
                call_args[0] == f"job {mock_job.function} with id '{mock_job.id}' {mock_job.status} after 1.0 seconds."
            )

        mock_clear.assert_called_once()
        mock_seconds.assert_called_once_with(log_ctx["total_runtime_ms"])

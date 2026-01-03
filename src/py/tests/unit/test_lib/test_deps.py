from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.lib import deps
from app.lib.deps import CompositeServiceMixin, provide_services


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


# --- Tests for provide_services ---


class MockService:
    """Mock service for testing."""

    def __init__(self, *, session: AsyncSession) -> None:
        self.session = session


async def mock_provider(session: AsyncSession) -> Any:
    """Mock provider that yields a MockService."""
    yield MockService(session=session)


@pytest.mark.asyncio
async def test_provide_services_raises_on_no_providers() -> None:
    """Test that provide_services raises ValueError when no providers given."""
    with pytest.raises(ValueError, match="At least one service provider is required"):
        async with provide_services():  # type: ignore[call-overload]
            pass


@pytest.mark.asyncio
async def test_provide_services_raises_on_both_session_and_connection() -> None:
    """Test that provide_services raises ValueError when both session and connection provided."""
    mock_session = MagicMock(spec=AsyncSession)
    mock_connection = MagicMock()

    with pytest.raises(ValueError, match="Cannot provide both 'session' and 'connection'"):
        async with provide_services(
            mock_provider,
            session=mock_session,
            connection=mock_connection,
        ):
            pass


@pytest.mark.asyncio
async def test_provide_services_with_explicit_session() -> None:
    """Test provide_services uses provided session without managing lifecycle."""
    mock_session = MagicMock(spec=AsyncSession)

    async with provide_services(mock_provider, session=mock_session) as (service,):
        assert isinstance(service, MockService)
        assert service.session is mock_session


@pytest.mark.asyncio
async def test_provide_services_standalone_mode() -> None:
    """Test provide_services creates and manages session in standalone mode."""
    mock_session = MagicMock(spec=AsyncSession)

    # Mock the alchemy config
    mock_alchemy = MagicMock()
    mock_alchemy.get_session = MagicMock()

    # Create an async context manager mock
    async def mock_get_session():
        yield mock_session

    from contextlib import asynccontextmanager

    mock_alchemy.get_session = asynccontextmanager(mock_get_session)

    with patch("app.lib.deps.alchemy", mock_alchemy, create=True):
        with patch.dict("sys.modules", {"app.config": MagicMock(alchemy=mock_alchemy)}):
            async with provide_services(mock_provider) as (service,):
                assert isinstance(service, MockService)
                assert service.session is mock_session


@pytest.mark.asyncio
async def test_provide_services_with_connection() -> None:
    """Test provide_services uses session from connection scope."""
    mock_session = MagicMock(spec=AsyncSession)
    mock_connection = MagicMock()
    mock_connection.app.state = MagicMock()
    mock_connection.scope = MagicMock()

    mock_alchemy = MagicMock()
    mock_alchemy.provide_session = MagicMock(return_value=mock_session)

    with patch.dict("sys.modules", {"app.config": MagicMock(alchemy=mock_alchemy)}):
        async with provide_services(mock_provider, connection=mock_connection) as (service,):
            assert isinstance(service, MockService)
            assert service.session is mock_session
            mock_alchemy.provide_session.assert_called_once_with(
                mock_connection.app.state,
                mock_connection.scope,
            )


@pytest.mark.asyncio
async def test_provide_services_multiple_providers() -> None:
    """Test provide_services with multiple providers sharing same session."""
    mock_session = MagicMock(spec=AsyncSession)

    class Service1:
        def __init__(self, *, session: AsyncSession) -> None:
            self.session = session

    class Service2:
        def __init__(self, *, session: AsyncSession) -> None:
            self.session = session

    async def provider1(session: AsyncSession) -> Any:
        yield Service1(session=session)

    async def provider2(session: AsyncSession) -> Any:
        yield Service2(session=session)

    async with provide_services(provider1, provider2, session=mock_session) as (svc1, svc2):
        assert isinstance(svc1, Service1)
        assert isinstance(svc2, Service2)
        # Both services should share the same session
        assert svc1.session is svc2.session
        assert svc1.session is mock_session


# --- Tests for CompositeServiceMixin ---


class DependentService:
    """Mock dependent service."""

    def __init__(self, *, session: AsyncSession) -> None:
        self.session = session


class ParentService(CompositeServiceMixin):
    """Mock parent service using the mixin."""

    def __init__(self, *, session: AsyncSession) -> None:
        # Simulate repository with session
        self.repository = MagicMock()
        self.repository.session = session

    @property
    def dependent(self) -> DependentService:
        return self._get_service(DependentService)


def test_composite_service_mixin_creates_dependent_service() -> None:
    """Test that _get_service creates a dependent service with shared session."""
    mock_session = MagicMock(spec=AsyncSession)
    parent = ParentService(session=mock_session)

    dependent = parent.dependent
    assert isinstance(dependent, DependentService)
    assert dependent.session is mock_session


def test_composite_service_mixin_caches_service() -> None:
    """Test that _get_service caches and returns same instance."""
    mock_session = MagicMock(spec=AsyncSession)
    parent = ParentService(session=mock_session)

    # Get the dependent service twice
    dependent1 = parent.dependent
    dependent2 = parent.dependent

    # Should be the same instance
    assert dependent1 is dependent2


def test_composite_service_mixin_caches_multiple_services() -> None:
    """Test that different dependent services are cached separately."""

    class AnotherService:
        def __init__(self, *, session: AsyncSession) -> None:
            self.session = session

    class MultiParentService(CompositeServiceMixin):
        def __init__(self, *, session: AsyncSession) -> None:
            self.repository = MagicMock()
            self.repository.session = session

        @property
        def dependent(self) -> DependentService:
            return self._get_service(DependentService)

        @property
        def another(self) -> AnotherService:
            return self._get_service(AnotherService)

    mock_session = MagicMock(spec=AsyncSession)
    parent = MultiParentService(session=mock_session)

    dependent = parent.dependent
    another = parent.another

    # Different types, different instances
    assert isinstance(dependent, DependentService)
    assert isinstance(another, AnotherService)
    assert dependent is not another

    # Both share the same session
    assert dependent.session is mock_session
    assert another.session is mock_session

    # Cached correctly
    assert parent.dependent is dependent
    assert parent.another is another

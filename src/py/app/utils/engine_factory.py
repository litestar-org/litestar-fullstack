from typing import TYPE_CHECKING, Any

from litestar.serialization import decode_json, encode_json
from sqlalchemy import NullPool, event
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

if TYPE_CHECKING:
    from app.lib.settings import DatabaseSettings


def create_sqlalchemy_engine(settings: "DatabaseSettings") -> "AsyncEngine":
    url = settings.URL.replace("postgresql://", "postgresql+psycopg://")
    if url.startswith("postgresql+asyncpg"):
        # Build engine kwargs - pool args are invalid with NullPool
        engine_kwargs: dict[str, Any] = {
            "url": url,
            "future": True,
            "json_serializer": encode_json,
            "json_deserializer": decode_json,
            "echo": settings.ECHO,
            "echo_pool": settings.ECHO_POOL,
            "pool_recycle": settings.POOL_RECYCLE,
            "pool_pre_ping": settings.POOL_PRE_PING,
        }
        if settings.POOL_DISABLED:
            engine_kwargs["poolclass"] = NullPool
        else:
            engine_kwargs.update(
                {
                    "max_overflow": settings.POOL_MAX_OVERFLOW,
                    "pool_size": settings.POOL_SIZE,
                    "pool_timeout": settings.POOL_TIMEOUT,
                    "pool_use_lifo": True,
                }
            )
        engine = create_async_engine(**engine_kwargs)
        """Database session factory.

        See [`async_sessionmaker()`][sqlalchemy.ext.asyncio.async_sessionmaker].
        """

        @event.listens_for(engine.sync_engine, "connect")
        def _sqla_on_connect(  # pragma: no cover # pyright: ignore[reportUnusedFunction]
            dbapi_connection: Any,
            _: Any,
        ) -> Any:  # pragma: no cover
            """Using msgspec for serialization of the json column values means that the
            output is binary, not `str` like `json.dumps` would output.
            SQLAlchemy expects that the json serializer returns `str` and calls `.encode()` on the value to
            turn it to bytes before writing to the JSONB column. I'd need to either wrap `serialization.to_json` to
            return a `str` so that SQLAlchemy could then convert it to binary, or do the following, which
            changes the behaviour of the dialect to expect a binary value from the serializer.
            See Also https://github.com/sqlalchemy/sqlalchemy/blob/14bfbadfdf9260a1c40f63b31641b27fe9de12a0/lib/sqlalchemy/dialects/postgresql/asyncpg.py#L934  pylint: disable=line-too-long
            """

            def encoder(bin_value: bytes) -> bytes:
                return b"\x01" + bin_value

            def decoder(bin_value: bytes) -> Any:
                # the byte is the \x01 prefix for jsonb used by PostgreSQL.
                # asyncpg returns it when format='binary'
                return decode_json(bin_value[1:])

            dbapi_connection.await_(
                dbapi_connection.driver_connection.set_type_codec(
                    "jsonb",
                    encoder=encoder,
                    decoder=decoder,
                    schema="pg_catalog",
                    format="binary",
                ),
            )
            dbapi_connection.await_(
                dbapi_connection.driver_connection.set_type_codec(
                    "json",
                    encoder=encoder,
                    decoder=decoder,
                    schema="pg_catalog",
                    format="binary",
                ),
            )

    elif url.startswith("sqlite+aiosqlite"):
        engine = create_async_engine(
            url=url,
            future=True,
            json_serializer=encode_json,
            json_deserializer=decode_json,
            echo=settings.ECHO,
            echo_pool=settings.ECHO_POOL,
            pool_recycle=settings.POOL_RECYCLE,
            pool_pre_ping=settings.POOL_PRE_PING,
        )
        """Database session factory.

        See [`async_sessionmaker()`][sqlalchemy.ext.asyncio.async_sessionmaker].
        """

        @event.listens_for(engine.sync_engine, "connect")
        def _sqla_on_connect(  # pragma: no cover # pyright: ignore[reportUnusedFunction]
            dbapi_connection: Any,
            _: Any,
        ) -> Any:
            """Override the default begin statement.  The disables the built in begin execution."""
            dbapi_connection.isolation_level = None

        @event.listens_for(engine.sync_engine, "begin")
        def _sqla_on_begin(  # pragma: no cover # pyright: ignore[reportUnusedFunction]
            dbapi_connection: Any,
        ) -> Any:
            """Emits a custom begin"""
            dbapi_connection.exec_driver_sql("BEGIN")

    else:
        # Build engine kwargs - pool args are invalid with NullPool
        engine_kwargs = {
            "url": url,
            "future": True,
            "json_serializer": encode_json,
            "json_deserializer": decode_json,
            "echo": settings.ECHO,
            "echo_pool": settings.ECHO_POOL,
            "pool_recycle": settings.POOL_RECYCLE,
            "pool_pre_ping": settings.POOL_PRE_PING,
        }
        if settings.POOL_DISABLED:
            engine_kwargs["poolclass"] = NullPool
        else:
            engine_kwargs.update(
                {
                    "max_overflow": settings.POOL_MAX_OVERFLOW,
                    "pool_size": settings.POOL_SIZE,
                    "pool_timeout": settings.POOL_TIMEOUT,
                    "pool_use_lifo": True,
                }
            )
        engine = create_async_engine(**engine_kwargs)
    return engine

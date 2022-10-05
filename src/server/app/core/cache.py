from asyncio import Lock
from dataclasses import dataclass
from datetime import datetime, timedelta
from fnmatch import fnmatch
from typing import Any, Dict, List, Optional, Tuple, Union, cast

from redis import RedisError
from redis.asyncio import Redis
from starlite import CacheConfig, Request
from starlite.cache.base import CacheBackendProtocol
from starlite.config.cache import default_cache_key_builder

from app.config import settings

redis = Redis.from_url(settings.cache.URL)


class RedisAsyncioBackend(CacheBackendProtocol):  # pragma: no cover
    """Cache Backend for Redis"""

    async def get(self, key: str) -> "Any":  # pylint: disable=invalid-overridden-method
        """Retrieve a value from cache corresponding to the given key."""
        return await redis.get(key)

    async def set(  # pylint: disable=invalid-overridden-method
        self, key: str, value: "Any", expiration: "Optional[Union[int, timedelta]]"
    ) -> "Any":
        """Set a value in cache for a given key with a given expiration in
        seconds."""
        return await redis.set(key, value, expiration)

    async def delete(self, key: str) -> "Any":  # pylint: disable=invalid-overridden-method
        """Remove a value from the cache for a given key."""
        return await redis.delete(key)

    async def scan(self, match: str, count: "Optional[int]" = None) -> "Tuple[int, list]":
        """Execute Redis SCAN command with pattern matching ."""
        return await redis.scan(match=match, count=count)

    async def keys(self, pattern: str) -> "list":
        """Find the keys matching a given pattern .

        If the keys do not exist the special value None is returned.
         An error is returned if the value stored at key is not a
        string, because GET only handles string values.
        """
        return await redis.keys(pattern)

    async def rpush(self, key: str, value: str, expiration: "Optional[Union[int, timedelta]]" = None) -> int:
        """Execute Redis RPUSH command.

        Insert all the specified values at the tail of the list stored at key.
        If key does not exist, it is created as empty list before performing
        the push operation. When key holds a value that is not a list, an
        error is returned.


        """

        if expiration:
            async with redis.pipeline(transaction=True) as pipe:
                push = await pipe.rpush(key, value)
                await pipe.expire(key, expiration).execute()
                return cast("int", push)
        else:
            return await redis.rpush(key, value)

    async def expire(self, key: str, expiration: "Union[int, timedelta]") -> bool:
        """Execute Redis EXPIRE command.

        Sets the TTL for a key.

        """
        return await redis.expire(key, expiration)

    async def exists(self, key: str) -> bool:
        """Execute Redis EXISTS command.

        Returns True if key exists.


        """
        cnt = await redis.exists(key)
        return cnt > 0

    async def mget(self, keys: "List[str]") -> "list[str | None]":
        """Execute Redis MGET command.

        Get the value of keys. If the keys do not exist the special value None
        is returned. An error is returned if the value stored at key is not a
        string, because GET only handles string values.



        """
        return await redis.mget(keys)

    async def lrange(self, key: str, start: int, end: int) -> "list":
        """Execute Redis LRANGE command.

        Returns the specified elements of the list stored at key. The offsets
        start and stop are zero-based indexes, with 0 being the first element
        of the list (the head of the list), 1 being the next element and so on.
        These offsets can also be negative numbers indicating offsets starting
        at the end of the list. For example, -1 is the last element of the
        list, -2 the penultimate, and so on.



        """
        return await redis.lrange(key, start, end)

    async def delete_keys(self, pattern: str) -> int:
        """Delete keys matching a pattern.

        Returns the number of keys deleted

        """
        async with redis.pipeline(transaction=True) as pipe:
            keys = await pipe.keys(pattern)
            deleted = await pipe.delete(*keys).execute()
            return cast("int", deleted)

    async def ping(self) -> bool:
        """Ping the Redis server."""
        try:
            return await redis.ping()
        except RedisError:
            return False


async def on_shutdown() -> None:
    """Passed to `Starlite.on_shutdown`."""
    await redis.close()


def cache_key_builder(request: Request) -> str:
    """Prefixes the default cache key with the app name.

    Parameters
    ----------
    request : Request

    Returns
    -------
    str
    """
    return f"{settings.app.NAME}:{default_cache_key_builder(request)}"


config = CacheConfig(
    backend=RedisAsyncioBackend(),
    expiration=settings.cache.EXPIRATION,
    cache_key_builder=cache_key_builder,
)


# WIP
@dataclass()
class CacheObject:
    """A container class for cache data."""

    value: Any
    """ cache data """
    expiration: datetime
    """ timestamp of cache """


class ExtendedSimpleCacheBackend(CacheBackendProtocol):
    def __init__(self) -> None:
        """This class offers a simple thread safe cache backend that stores
        values in local memory using a `dict`."""
        self._store: Dict[str, CacheObject] = {}
        self._lock = Lock()

    async def get(self, key: str) -> Any:  # pylint: disable=invalid-overridden-method
        """Retrieve value from cache corresponding to the given key.

        Args:
            key: name of cached value.

        Returns:
            Cached value or `None`.
        """
        async with self._lock:
            cache_obj = self._store.get(key)

        if cache_obj:
            if cache_obj.expiration >= datetime.now():
                return cache_obj.value
            await self.delete(key)

        return None

    async def set(self, key: str, value: Any, expiration: int) -> None:  # pylint: disable=invalid-overridden-method
        """Set a value in cache for a given key with a given expiration in
        seconds.

        Args:
            key: key to cache `value` under.
            value: the value to be cached.
            expiration: expiration of cached value in seconds.

        Returns:
            None
        """
        async with self._lock:
            self._store[key] = CacheObject(value=value, expiration=datetime.now() + timedelta(seconds=expiration))

        return None

    async def delete(self, key: str) -> None:  # pylint: disable=invalid-overridden-method
        """Remove a value from the cache for a given key.

        Args:
            key: key to be deleted from the cache.

        Returns:
            None
        """
        async with self._lock:
            self._store.pop(key, None)
        return None

    async def scan(self, match: str, count: "Optional[int]" = None) -> "Tuple[int, list[Any]]":
        """Execute Redis SCAN command with pattern matching ."""
        async with self._lock:
            matches = [v for k, v in self._store.items() if fnmatch(k, match)]
            return (len(matches), matches)

    async def keys(self, pattern: str) -> "list[str]":
        """Find the keys matching a given pattern .

        If the keys do not exist None is returned.
        """
        async with self._lock:
            return [k for k, _ in self._store.items() if fnmatch(k, pattern)]

    async def rpush(self, key: str, value: str, expiration: "Optional[Union[int, timedelta]]" = None) -> int:
        """Execute Redis RPUSH command.

        Insert all the specified values at the tail of the list stored at key.
        If key does not exist, it is created as empty list before performing
        the push operation. When key holds a value that is not a list, an
        error is returned.


        """

        if expiration:
            async with redis.pipeline(transaction=True) as pipe:
                push = await pipe.rpush(key, value)
                await pipe.expire(key, expiration).execute()
                return cast("int", push)
        else:
            return await redis.rpush(key, value)

    async def expire(self, key: str, expiration: "Union[int, timedelta]") -> bool:
        """Execute Redis EXPIRE command.

        Sets the TTL for a key.

        """
        return await redis.expire(key, expiration)

    async def exists(self, key: str) -> bool:
        """Execute Redis EXISTS command.

        Returns True if key exists.


        """
        cnt = await redis.exists(key)
        return cnt > 0

    async def mget(self, keys: "List[str]") -> "list[str | None]":
        """Execute Redis MGET command.

        Get the value of keys. If the keys do not exist the special value None
        is returned. An error is returned if the value stored at key is not a
        string, because GET only handles string values.



        """
        return await redis.mget(keys)

    async def lrange(self, key: str, start: int, end: int) -> "list":
        """Execute Redis LRANGE command.

        Returns the specified elements of the list stored at key. The offsets
        start and stop are zero-based indexes, with 0 being the first element
        of the list (the head of the list), 1 being the next element and so on.
        These offsets can also be negative numbers indicating offsets starting
        at the end of the list. For example, -1 is the last element of the
        list, -2 the penultimate, and so on.



        """
        return await redis.lrange(key, start, end)

    async def delete_keys(self, pattern: str) -> int:
        """Delete keys matching a pattern.

        Returns the number of keys deleted

        """
        async with redis.pipeline(transaction=True) as pipe:
            keys = await pipe.keys(pattern)
            deleted = await pipe.delete(*keys).execute()
            return cast("int", deleted)

    async def ping(self) -> bool:
        """Simple ping test use for health checks."""
        return True

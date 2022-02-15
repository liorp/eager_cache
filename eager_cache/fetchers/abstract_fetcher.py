from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from aiocache import Cache
from aiocache.serializers import JsonSerializer
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel

from eager_cache.settings import Settings

DEFAULT_TTL = 3600


def get_cache_key(data_type: str, **kwargs: Any) -> str:
    """
    Gets the cache key for the data type and kwargs.

    :param data_type: Data type for cache key
    :param kwargs: Kwargs for cache key
    :return: Cache key
    """
    cache_key = f"{data_type}"
    for key in kwargs.keys():
        if kwargs[key] is not None:
            cache_key = f"{cache_key}_{key}_{kwargs[key]}"
    return cache_key


class DataItem(BaseModel):
    """
    Model representation of data item.

    Comprised of three elements: the data itself, retrieve time from your data source,
    and the time when the data itself was last modified.
    """

    data_item: Any  # The data itself

    last_retrieved: datetime  # This is the retrieve time from your data source.
    # Do not confuse with `last_modified`, which is when the data itself was modified.

    last_modified: datetime  # This is the time when the data itself was last modified.
    # Do not confuse with `last_retrieved`, which is when the data itself was retrieved.


class AbstractFetcher(ABC):
    """
    Inherit from this class in order to add fetchers.

    Note that you should implement only the _fetch function.
    """

    data_type: str  # this will be used to cache the request
    ttl: int = (
        DEFAULT_TTL  # time for cache invalidation, in seconds (default is 1 hour)
    )

    cache = Cache(
        Cache.REDIS,
        url=Settings.redis_url,
        serializer=JsonSerializer(),
        namespace="fetchers",
    )

    @classmethod
    async def fetch(cls, **kwargs: Any) -> DataItem:
        """
        Wraps the internal _fetch logic with eager caching.

        :param **kwargs: Arbitrary keyword arguments.
        :return: Data item.
        """
        cache_key = get_cache_key(cls.data_type, **kwargs)
        cached_result = await cls.cache.get(cache_key)
        if cached_result is None:
            fetched_result = await cls._fetch(**kwargs)
            cached_result = await cls.cache.set(
                cache_key,
                jsonable_encoder(fetched_result),
            )
        return cached_result

    @abstractmethod
    @classmethod
    async def _fetch(cls, **kwargs: Any) -> DataItem:
        # The internal fetch method you need to override.
        raise NotImplementedError

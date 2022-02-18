from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Tuple

from aiocache import Cache
from aiocache.serializers import JsonSerializer
from deepdiff import DeepDiff
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel

DEFAULT_TTL = 3600
SHADOW_KEY_PREFIX = "shadow:"


def get_cache_key(data_type: str, **kwargs: Any) -> Tuple[str, str]:
    """
    Gets the cache key for the data type and kwargs.

    :param data_type: Data type for cache key
    :param kwargs: Kwargs for cache key
    :return: Cache key and shadow cache key
    """
    cache_key = f"{data_type}"
    for key in kwargs.keys():
        if kwargs[key] is not None:
            cache_key = f"{cache_key}_{key}_{kwargs[key]}"
    return cache_key, SHADOW_KEY_PREFIX + cache_key


class DataItem(BaseModel):
    """
    Model representation of data item.

    Comprised of three elements: the data itself, the retrieve time from data source,
    and the time when the data itself was last modified.
    """

    data_item: Any  # The data itself

    last_retrieved: datetime  # This is the retrieve time from data source.
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
        Cache.MEMORY,
        # url=Settings.redis_url, TODO: SET THIS TO REDIS
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
        cache_key, shadow_cache_key = get_cache_key(cls.data_type, **kwargs)
        shadow = await cls.cache.get(shadow_cache_key)
        if shadow is None:
            # If we don't have a shadow key, it means that the data has expird or never been fetched.
            # Either way, we need to refetch the data.
            fetched_data = jsonable_encoder(await cls._fetch(**kwargs))

            # Check if the data has been modified since last retrieved
            previous_cached_result = jsonable_encoder(
                await cls.cache.get(shadow_cache_key),
            )
            last_modified = datetime.now()
            if previous_cached_result is not None:
                previous_data = previous_cached_result["data_item"]
                if DeepDiff(previous_data, fetched_data) == {}:
                    last_modified = previous_cached_result["last_modified"]

            # Finally, set the data and the shadow in the cache
            cached_result = await cls.cache.set(
                cache_key,
                DataItem(
                    last_modified=last_modified,
                    last_retrieved=datetime.now(),
                    data=fetched_data,
                ),
            )
            await cls.cache.set(SHADOW_KEY_PREFIX, "")
            return cached_result

        return await cls.cache.get(cache_key)

    @classmethod
    @abstractmethod
    async def _fetch(cls, **kwargs: Any) -> Any:
        # The internal fetch method you need to override.
        raise NotImplementedError

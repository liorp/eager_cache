import json
import random
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Tuple
from urllib.parse import urlencode

from aioredis import Redis
from deepdiff import DeepDiff
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel

from eager_cache.log_utils import fetchers_logger

# Default values for caching
# Note: these values can put a lot of stress on the server, since they are low. Change them as you profile your usage.
DEFAULT_TTL = 10
DEFAULT_JITTER = 5
SEPARATOR = ":"
SHADOW_KEY_PREFIX = "shadow"


def get_cache_keys(data_type: str, **kwargs: Any) -> Tuple[str, str]:
    """
    Gets the cache key for the data type and kwargs.
    The formula is quite simple: it concatenates the data_type with the list of kwargs

    :param data_type: Data type for cache key
    :param kwargs: Kwargs for cache key
    :return: Cache key and shadow cache key
    """
    cache_key = f"{data_type}"
    for key in kwargs.keys():
        if kwargs[key] is not None:
            cache_key = (
                f"{cache_key}" + SEPARATOR + f"{key}" + SEPARATOR + f"{kwargs[key]}"
            )
    return cache_key, SHADOW_KEY_PREFIX + SEPARATOR + cache_key


def decode_shadow_cache_key(shadow_cache_key: str):
    """
    Given a shadow cache key, calculates the fetch data url.
    This is useful for fetching the data if it has gone stale (e.g. the shadow key has expired)

    :param shadow_cache_key: The shadow cache key
    :return: The url to refetch the data
    """
    cache_key = shadow_cache_key.split(SEPARATOR)[1:]
    data_type = cache_key[0]
    raw_query = cache_key[1:]
    query = {}

    # Split the query to tuples
    for i in range(0, len(raw_query), 2):
        query[raw_query[i]] = raw_query[i + 1]

    return f"/{data_type}?{urlencode(query)}"


class DataItem(BaseModel):
    """
    Model representation of data item.

    Comprised of three elements: the data itself, the retrieve time from data source,
    and the time when the data itself was last modified.
    """

    data: Any  # The data itself

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
        DEFAULT_TTL  # time for cache invalidation, in seconds (default is 10 seconds)
    )
    jitter: int = DEFAULT_JITTER  # jitter time for cache invalidation, in seconds (default is 5 seconds)
    serializer = json  # override this with your preferred serializer. should support loads and dumps.

    @classmethod
    async def fetch(cls, redis: Redis, **kwargs: Any) -> DataItem:
        """
        Wraps the internal _fetch logic with eager caching.
        We use a [shadow key](https://stackoverflow.com/a/28647773/938227) for each record, which indicates whether the cached data is valid.
        If the shadow key doesn't exist, we fetch the data and return it.
        If the shadow key exists, we just return the cached data.

        :param **kwargs: Arbitrary keyword arguments.
        :return: Data item.
        """
        cache_key, shadow_cache_key = get_cache_keys(cls.data_type, **kwargs)
        fetchers_logger.info(
            f"Got key: {cache_key}, shadow: {shadow_cache_key}",
            extra={"cahce_key": cache_key, "shadow_cache_key": shadow_cache_key},
        )
        shadow = await redis.get(name=shadow_cache_key)
        if shadow is None:
            # If we don't have a shadow key, it means that the data has either expired or never been fetched.
            # Either way, we need to refetch the data.
            fetched_data = await cls._fetch(**kwargs)
            fetchers_logger.info(
                "Fetched new data",
                extra={"cahce_key": cache_key, "fetched_data": fetched_data},
            )

            # Check if the data has been modified since last retrieved
            previous_cached_result = await redis.get(name=cache_key)

            # Calculate the last_modified time
            last_modified = cls.calculate_last_modified(
                cache_key,
                fetched_data,
                previous_cached_result,
            )

            data_item = DataItem(
                last_modified=last_modified,
                last_retrieved=datetime.now(),
                data=fetched_data,
            )

            # Finally, set the data and the shadow in the cache
            await cls.set_cache_data_and_shadow(
                redis,
                cache_key,
                shadow_cache_key,
                data_item,
            )
            fetchers_logger.info(
                "Cached data",
                extra={"cahce_key": cache_key, "data": fetched_data},
            )

            return data_item

        return DataItem(**cls.serializer.loads(await redis.get(name=cache_key)))

    @classmethod
    async def set_cache_data_and_shadow(
        cls,
        redis,
        cache_key,
        shadow_cache_key,
        data_item,
    ):
        await redis.set(
            cache_key,
            cls.serializer.dumps(jsonable_encoder(data_item)),
        )
        await redis.set(
            name=shadow_cache_key,
            value="",
            ex=cls.ttl + random.randint(0, cls.jitter),
        )

    @classmethod
    def calculate_last_modified(
        cls,
        cache_key: str,
        fetched_data: Any,
        previous_cached_result: Any,
    ) -> datetime:
        """
        Compares `fetched_data` to `previous_cached_result["data"]` and returns the modification date.

        :param cache_key: The cache key of the data.
        :param fetched_data: Freshly fetched data.
        :param previous_cached_result: The previous cached result from redis.
        :return: When was the data modified.
        :return type: datetime
        """
        last_modified = datetime.now()
        if previous_cached_result is not None:
            # If we have data in the cache, load and compare it to the freshly fetched data
            json_previous_cached_result = cls.serializer.loads(
                previous_cached_result,
            )
            last_modified = datetime.fromisoformat(
                json_previous_cached_result["last_modified"],
            )
            previous_data = json_previous_cached_result["data"]
            if DeepDiff(previous_data, fetched_data) != {}:
                fetchers_logger.info(
                    "Data has been modified since last fetch",
                    extra={
                        "cahce_key": cache_key,
                    },
                )
                last_modified = datetime.now()
        return last_modified

    @classmethod
    @abstractmethod
    async def _fetch(cls, **kwargs: Any) -> Any:
        # The internal fetch method you need to override.
        raise NotImplementedError

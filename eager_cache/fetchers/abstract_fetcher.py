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

DEFAULT_TTL = 10
DEFAULT_JITTER = 5
SHADOW_KEY_PREFIX = "shadow:"


def get_cache_keys(data_type: str, **kwargs: Any) -> Tuple[str, str]:
    """
    Gets the cache key for the data type and kwargs.

    :param data_type: Data type for cache key
    :param kwargs: Kwargs for cache key
    :return: Cache key and shadow cache key
    """
    cache_key = f"{data_type}"
    for key in kwargs.keys():
        if kwargs[key] is not None:
            cache_key = f"{cache_key}:{key}:{kwargs[key]}"
    return cache_key, SHADOW_KEY_PREFIX + cache_key


def decode_shadow_cache_key(shadow_cache_key: str):
    """
    Given a shadow cache key, calculates the fetch data url.

    :param shadow_cache_key: The shadow cache key
    :return: The url to refetch the data
    """
    cache_key = shadow_cache_key.split(":")[1:]
    data_type = cache_key[0]
    raw_query = cache_key[1:]
    query = {}

    # Split the query to tuples
    # TODO: Make this better
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
            last_modified = datetime.now()
            if previous_cached_result is not None:
                json_previous_cached_result = cls.serializer.loads(
                    previous_cached_result,
                )
                previous_data = json_previous_cached_result["data"]
                if DeepDiff(previous_data, fetched_data) == {}:
                    fetchers_logger.info(
                        "Data has modified since last fetch",
                        extra={
                            "cahce_key": cache_key,
                        },
                    )
                    last_modified = json_previous_cached_result["last_modified"]

            data_item = DataItem(
                last_modified=last_modified,
                last_retrieved=datetime.now(),
                data=fetched_data,
            )

            # Finally, set the data and the shadow in the cache
            await redis.set(
                cache_key,
                cls.serializer.dumps(jsonable_encoder(data_item)),
            )
            await redis.set(
                name=shadow_cache_key,
                value="",
                ex=cls.ttl + random.randint(0, cls.jitter),
            )
            fetchers_logger.info(
                "Set cache",
                extra={
                    "cahce_key": cache_key,
                },
            )

            return data_item

        return DataItem(**cls.serializer.loads(await redis.get(name=cache_key)))

    @classmethod
    @abstractmethod
    async def _fetch(cls, **kwargs: Any) -> Any:
        # The internal fetch method you need to override.
        raise NotImplementedError

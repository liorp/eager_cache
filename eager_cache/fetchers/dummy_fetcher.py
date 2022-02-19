from asyncio import sleep
from typing import Any

from eager_cache.fetchers.abstract_fetcher import AbstractFetcher


class DummyFetcher(AbstractFetcher):
    """
    A dummy fetcher class.

    Does nothing but sleep, in order to demonstrate the caching.
    """

    data_type = "dummy"

    @classmethod
    async def _fetch(cls, **kwargs: Any) -> Any:
        # The internal fetch method you need to override.
        await sleep(5)
        return kwargs

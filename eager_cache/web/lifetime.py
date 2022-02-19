from typing import Awaitable, Callable

import aioredis
from fastapi import FastAPI

from eager_cache.settings import settings


def _setup_redis(app: FastAPI) -> None:
    """
    Initialize redis connection.

    :param app: current FastAPI app.
    """
    app.state.redis_pool = aioredis.ConnectionPool.from_url(
        str(settings.redis_url),
    )


def startup(app: FastAPI) -> Callable[[], Awaitable[None]]:
    """
    Actions to run on application startup.

    This function use fastAPI app to store data,
    such as db_engine.

    :param app: the fastAPI application.
    :return: function that actually performs actions.
    """

    async def _startup() -> None:  # noqa: WPS430
        _setup_redis(app)
        pass  # noqa: WPS420

    return _startup


def shutdown(app: FastAPI) -> Callable[[], Awaitable[None]]:
    """
    Actions to run on application's shutdown.

    :param app: fastAPI application.
    :return: function that actually performs actions.
    """

    async def _shutdown() -> None:  # noqa: WPS430
        await app.state.redis_pool.disconnect()
        pass  # noqa: WPS420

    return _shutdown

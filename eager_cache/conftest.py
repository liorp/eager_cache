import asyncio
import sys
from typing import Generator

import nest_asyncio
import pytest
from fakeredis.aioredis import FakeRedis
from fastapi import FastAPI
from fastapi.testclient import TestClient

from eager_cache.services.redis.dependency import get_redis_connection
from eager_cache.web.application import get_app

nest_asyncio.apply()


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """
    Create an instance of event loop for tests.

    This hack is required in order to get `dbsession` fixture to work.
    Because default fixture `event_loop` is function scoped,
    but dbsession requires session scoped `event_loop` fixture.

    :yields: event loop.
    """
    python_version = sys.version_info[:2]
    if sys.platform.startswith("win") and python_version >= (3, 8):
        # Avoid "RuntimeError: Event loop is closed" on Windows when tearing down tests
        # https://github.com/encode/httpx/issues/914
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture()
def fake_redis() -> FakeRedis:
    """
    Get instance of a fake redis.

    :return: FakeRedis instance.
    """
    return FakeRedis(decode_responses=True)


@pytest.fixture()
def fastapi_app(
    fake_redis: FakeRedis,
) -> FastAPI:
    """
    Fixture for creating FastAPI app.

    :return: fastapi app with mocked dependencies.
    """
    application = get_app()

    application.dependency_overrides[get_redis_connection] = lambda: fake_redis

    return application


@pytest.fixture(scope="function")
def client(
    fastapi_app: FastAPI,
) -> TestClient:
    """
    Fixture that creates client for requesting server.

    :param fastapi_app: the application.
    :return: client for the app.
    """
    return TestClient(app=fastapi_app)

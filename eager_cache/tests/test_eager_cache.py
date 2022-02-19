from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette import status

from eager_cache.fetchers.abstract_fetcher import (
    decode_shadow_cache_key,
    get_cache_keys,
)


def test_health(client: TestClient, fastapi_app: FastAPI) -> None:
    """
    Checks the health endpoint.

    :param client: client for the app.
    :param fastapi_app: current FastAPI application.
    """
    url = fastapi_app.url_path_for("health_check")
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK


def test_get_cache_keys() -> None:
    assert get_cache_keys("dummy", a="b") == ("dummy:a:b", "shadow:dummy:a:b")


def test_decode_shadow_cache_key() -> None:
    assert decode_shadow_cache_key("shadow:dummy:a:b") == "/dummy?a=b"

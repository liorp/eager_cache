import json
from datetime import datetime

from fastapi import FastAPI
from fastapi.testclient import TestClient
from freezegun import freeze_time
from starlette import status

from eager_cache.fetchers.abstract_fetcher import (
    AbstractFetcher,
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


@freeze_time("2020-01-14")
def test_calculate_last_modified__modified() -> None:
    fetched_data = {"a": "b"}
    cached_data = json.dumps(
        {"data": {"a": "c"}, "last_modified": datetime(2019, 1, 1).isoformat()},
    )

    assert (
        AbstractFetcher.calculate_last_modified(
            "dummy:a:b",
            fetched_data,
            cached_data,
        ).isoformat()
        == datetime(2020, 1, 14).isoformat()
    )


@freeze_time("2020-01-14")
def test_calculate_last_modified__unmodified() -> None:
    fetched_data = {"a": "c"}
    cached_data = json.dumps(
        {"data": {"a": "c"}, "last_modified": datetime(2019, 1, 1).isoformat()},
    )

    assert (
        AbstractFetcher.calculate_last_modified(
            "dummy:a:b",
            fetched_data,
            cached_data,
        ).isoformat()
        == datetime(2019, 1, 1).isoformat()
    )

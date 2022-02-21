from threading import Thread
from typing import TypedDict

import requests
from redis import Redis
from redis.client import PubSub

from eager_cache.fetchers.abstract_fetcher import decode_shadow_cache_key
from eager_cache.settings import settings
from log_utils import update_cache_logger

redis = Redis(
    host=settings.redis_host,
    port=settings.redis_port,
    username=settings.redis_user,
    password=settings.redis_pass,
)


class KeyeventMessage(TypedDict):
    type: str
    pattern: bytes
    channel: bytes
    data: bytes


def event_handler(event: KeyeventMessage) -> None:
    """
    Receives the expire keyevent from redis, and issues a request to refetch the corresponding data from the server.

    :param event: The keyspace event.
    """
    update_cache_logger.info(f"Received event {event}", extra={"event": event})
    key = event["data"].decode()
    data_fetch_url = decode_shadow_cache_key(key)
    full_url = (
        f"{settings.protocol}://{settings.host}:{settings.port}/api/data"
        + data_fetch_url
    )
    update_cache_logger.info(
        f"Got data url {data_fetch_url}",
        extra={"data_fetch_url": data_fetch_url},
    )
    r = requests.get(full_url)
    update_cache_logger.info(
        f"Sent request to {data_fetch_url}, code: {r.status_code}, response: {r.json()}",
        extra={"data_fetch_url": data_fetch_url, "code": r, "response": r.json()},
    )


def exception_handler(ex: Exception, pubsub: PubSub, thread: Thread) -> None:
    update_cache_logger.exception(exc_info=ex)
    thread.stop()
    thread.join(timeout=1.0)
    pubsub.close()


def main():
    pubsub = redis.pubsub()
    pubsub.psubscribe(**{"__keyevent@0__:expired": event_handler})
    pubsub.run_in_thread(sleep_time=0.01)
    update_cache_logger.info(
        f"Started update cache microservice",
    )


if __name__ == "__main__":
    main()

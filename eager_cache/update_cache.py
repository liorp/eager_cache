from typing import Any

from redis import Redis

from eager_cache.settings import settings

redis = Redis(
    host=settings.redis_host,
    port=settings.redis_port,
    username=settings.redis_user,
    password=settings.redis_pass,
)


def event_handler(msg: Any) -> None:
    print(msg)
    thread.stop()


pubsub = redis.pubsub()
pubsub.psubscribe(**{"__keyevent@0__:expired": event_handler})
thread = pubsub.run_in_thread(sleep_time=0.01)

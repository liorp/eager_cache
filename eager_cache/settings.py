from pathlib import Path
from tempfile import gettempdir
from typing import Optional

from pydantic import BaseSettings
from yarl import URL

TEMP_DIR = Path(gettempdir())


class Settings(BaseSettings):
    """Application settings."""

    host: str = "127.0.0.1"
    port: int = 8000
    # quantity of workers for uvicorn
    workers_count: int = 1
    # Enable uvicorn reloading
    reload: bool = False
    redis_host: str = "eager_cache-redis"
    redis_port: int = 6379
    redis_user: Optional[str] = None
    redis_pass: Optional[str] = None
    redis_base: Optional[int] = None

    @property
    def redis_url(self) -> URL:
        """
        Assemble REDIS URL from settings.

        :return: redis URL.
        """
        path = ""
        if self.redis_base is not None:
            path = f"/{self.redis_base}"
        return URL.build(
            scheme="redis",
            host=self.redis_host,
            port=self.redis_port,
            user=self.redis_user,
            password=self.redis_pass,
            path=path,
        )

    class Config:
        env_file = ".env"
        env_prefix = "EAGER_CACHE_"
        env_file_encoding = "utf-8"


settings = Settings()

"""Shared rate limiter instance."""
from slowapi import Limiter
from slowapi.util import get_remote_address

from src.config import settings


def _build_storage_uri() -> str:
    if settings.ENVIRONMENT == "testing" or not settings.REDIS_URL:
        return "memory://"
    return settings.REDIS_URL


limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["10000/hour"] if settings.DEBUG or settings.ENVIRONMENT == "testing" else ["1000/hour"],
    storage_uri=_build_storage_uri(),
)

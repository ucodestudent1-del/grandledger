"""Shared rate limiter instance."""
from __future__ import annotations

import logging

from slowapi import Limiter
from slowapi.util import get_remote_address

from src.config import settings

logger = logging.getLogger("grandledger")


def _build_storage_uri() -> str:
    if settings.ENVIRONMENT == "testing" or not settings.REDIS_URL:
        return "memory://"

    parsed = settings.REDIS_URL
    if parsed.startswith("redis"):
        try:
            import redis

            client = redis.from_url(parsed, socket_connect_timeout=1)
            client.ping()
            return parsed
        except Exception:
            logger.warning("Redis not available, disabling rate limiting")
            return "memory://"
    return parsed


limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["10000/hour"] if settings.DEBUG or settings.ENVIRONMENT == "testing" else ["500/hour"],
    storage_uri=_build_storage_uri(),
)

# Rate limit presets for different endpoint types
AUTH_RATE_LIMIT = "10/minute" if settings.ENVIRONMENT == "testing" else "5/minute"
API_WRITE_RATE_LIMIT = "1000/hour" if settings.ENVIRONMENT == "testing" else "100/hour"
API_READ_RATE_LIMIT = "5000/hour" if settings.ENVIRONMENT == "testing" else "500/hour"

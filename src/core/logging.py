"""Structured logging configuration using structlog."""
from __future__ import annotations

import logging
import sys

from src.config import settings


def configure_logging() -> None:
    """Configure structured JSON logging for production."""
    log_level = logging.DEBUG if settings.DEBUG else logging.INFO

    if settings.ENVIRONMENT == "testing":
        logging.basicConfig(level=log_level, format="%(message)s")
        return

    try:
        import structlog

        structlog.configure(
            processors=[
                structlog.contextvars.merge_contextvars,
                structlog.processors.add_log_level,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.JSONRenderer(),
            ],
            wrapper_class=structlog.make_filtering_bound_logger(log_level),
            context_class=dict,
            logger_factory=structlog.WriteLoggerFactory(file=sys.stdout),
        )
        logging.basicConfig(
            level=log_level,
            format="%(message)s",
            stream=sys.stdout,
        )
    except ImportError:
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            stream=sys.stdout,
        )


def get_logger(name: str = "grandledger") -> logging.Logger:
    return logging.getLogger(name)

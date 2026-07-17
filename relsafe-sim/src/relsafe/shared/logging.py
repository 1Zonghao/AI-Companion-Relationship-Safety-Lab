"""Structured logging setup for the simulation."""

from __future__ import annotations

import logging
import os


def get_log_level() -> int:
    """Return the configured log level from RELSAFE_LOG_LEVEL env var."""
    level = os.environ.get("RELSAPE_LOG_LEVEL", "INFO").upper()
    return getattr(logging, level, logging.INFO)


def configure_logging(level: int | None = None) -> None:
    """Configure Python standard logging for the RelSafe package."""
    if level is None:
        level = get_log_level()
    fmt = os.environ.get("RELSAPE_LOG_FORMAT", "text")

    if fmt == "json":
        # Minimal JSON-line logging — full structlog can be added later
        logging.basicConfig(
            level=level,
            format='{"time": "%(asctime)s", "level": "%(levelname)s", "name": "%(name)s", "msg": "%(message)s"}',
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
    else:
        logging.basicConfig(
            level=level,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )


def get_logger(name: str) -> logging.Logger:
    """Return a logger for the given module name."""
    return logging.getLogger(name)

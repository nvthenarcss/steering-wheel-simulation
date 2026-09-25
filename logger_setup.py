"""Rotating file logger + console handler, actually wired into the app this time."""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from config import config

_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
}


def get_logger(name: str = "gaming_steering") -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        # Already configured (e.g. imported from multiple modules) — reuse it.
        return logger

    level = _LEVELS.get(config.get("logging", "level", default="INFO"), logging.INFO)
    logger.setLevel(level)

    log_path = Path(config.get("logging", "file", default=str(Path.home() / ".gaming_steering" / "app.log")))
    log_path.parent.mkdir(parents=True, exist_ok=True)

    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s", "%H:%M:%S")

    file_handler = RotatingFileHandler(log_path, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(fmt)
    logger.addHandler(console_handler)

    return logger

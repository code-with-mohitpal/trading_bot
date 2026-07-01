"""
logging_config.py

Centralized logging configuration for the trading bot.

All API requests, responses, and errors are logged to `logs/trading_bot.log`
using a rotating file handler so log files don't grow unbounded. A console
handler is also attached so the operator gets immediate feedback while the
full detail is preserved in the log file.
"""

import logging
import os
from logging.handlers import RotatingFileHandler

# Directory where log files are stored (created if it doesn't exist)
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
LOG_FILE = os.path.join(LOG_DIR, "trading_bot.log")

# Keep log files reasonably sized: 5 MB per file, 3 backups kept
MAX_BYTES = 5 * 1024 * 1024
BACKUP_COUNT = 3

_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(log_level: int = logging.INFO) -> logging.Logger:
    """
    Configure and return the root logger for the trading bot.

    Idempotent: calling this multiple times will not attach duplicate
    handlers (useful since both cli.py and main.py may call it).

    Args:
        log_level: Logging level for the file handler (default INFO).

    Returns:
        The configured "trading_bot" logger instance.
    """
    os.makedirs(LOG_DIR, exist_ok=True)

    logger = logging.getLogger("trading_bot")
    logger.setLevel(log_level)

    # Avoid attaching duplicate handlers if setup_logging() is called twice
    if logger.handlers:
        return logger

    formatter = logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT)

    # Rotating file handler -> logs/trading_bot.log
    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=MAX_BYTES, backupCount=BACKUP_COUNT, encoding="utf-8"
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)

    # Console handler -> stdout, human-friendly summary level
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logger.propagate = False

    return logger


def get_logger() -> logging.Logger:
    """Convenience accessor used by other modules to fetch the shared logger."""
    return logging.getLogger("trading_bot")

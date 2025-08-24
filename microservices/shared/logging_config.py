"""
Logging configuration for microservices
"""

import logging
import sys
from typing import Optional


def setup_logger(
    name: str, level: str = "INFO", format_string: Optional[str] = None
) -> logging.Logger:
    """Setup logger for microservice"""

    if format_string is None:
        format_string = (
            "%(asctime)s - %(name)s - %(levelname)s - "
            "%(funcName)s:%(lineno)d - %(message)s"
        )

    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))
    formatter = logging.Formatter(format_string)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger

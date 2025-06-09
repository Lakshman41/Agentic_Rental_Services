# File: agentic_rental_platform/app/core/logging.py
import logging
import sys
from app.core.config import settings

LOG_LEVEL_STR = settings.LOG_LEVEL.upper()
numeric_level = getattr(logging, LOG_LEVEL_STR, None)

if not isinstance(numeric_level, int):
    numeric_level = logging.INFO

logger = logging.getLogger(settings.APP_NAME)
logger.setLevel(numeric_level)

if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(numeric_level)
    formatter = logging.Formatter(
        "[%(asctime)s] [%(name)s] [%(levelname)s] [%(module)s:%(lineno)d] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
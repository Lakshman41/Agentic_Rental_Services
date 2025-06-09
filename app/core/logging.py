# File: agentic_rental_platform/app/core/logging.py
import logging
import sys
from app.core.config import settings # Will load from .env via pydantic-settings

# Determine log level from settings
LOG_LEVEL_STR = settings.LOG_LEVEL.upper()
numeric_level = getattr(logging, LOG_LEVEL_STR, None)

# Default to INFO if the LOG_LEVEL string is invalid
if not isinstance(numeric_level, int):
    numeric_level = logging.INFO
    # print(f"Warning: Invalid LOG_LEVEL '{settings.LOG_LEVEL}'. Defaulting to INFO.", file=sys.stderr) # Optional warning

# Create a logger instance for the application
# Using settings.APP_NAME ensures the logger is named after your application.
logger = logging.getLogger(settings.APP_NAME)
logger.setLevel(numeric_level)

# Prevent adding multiple handlers if this module is imported multiple times
# (e.g., during Uvicorn reload or by different parts of the app initializing logging)
if not logger.handlers:
    # Create a handler for stdout (console output)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(numeric_level)

    # Create a formatter and set it for the handler
    # Example format: [TIMESTAMP] [APP_NAME] [LEVEL] [MODULE:LINENO] MESSAGE
    formatter = logging.Formatter(
        "[%(asctime)s] [%(name)s] [%(levelname)s] [%(module)s:%(lineno)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)

    # Add the handler to the logger
    logger.addHandler(handler)

# else:
    # logger.debug(f"Logger '{settings.APP_NAME}' already has handlers configured.") # Optional debug message

# Example usage in other modules:
# from app.core.logging import logger
# logger.info("This is an info message from the app logger.")
# logger.debug("This is a debug message.") # Will only show if LOG_LEVEL is DEBUG
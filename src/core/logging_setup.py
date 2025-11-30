""
Logging setup for ChicoBot.

This module configures logging for the application with appropriate handlers,
formatters, and log levels. It provides a consistent way to log messages
throughout the application.
"""
import logging
import sys
import os
from logging.handlers import RotatingFileHandler
from typing import Optional, Dict, Any

from config import get_settings, LogMessages

# Get application settings
settings = get_settings()

# Log formats
CONSOLE_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
FILE_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
JSON_FORMAT = (
    '{"timestamp":"%(asctime)s", "name":"%(name)s", "level":"%(levelname)s", '
    '"message":"%(message)s", "module":"%(module)s", "function":"%(funcName)s", '
    '"line":%(lineno)d, "process":%(process)d, "thread":%(thread)d}'
)

# Log levels as strings to logging levels
LOG_LEVELS = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL,
}

def get_log_level() -> int:
    """Get the logging level from settings.
    
    Returns:
        int: The logging level.
    """
    return LOG_LEVELS.get(settings.LOG_LEVEL.upper(), logging.INFO)

def setup_logging(
    name: str = "chicobot",
    log_level: Optional[int] = None,
    log_file: Optional[str] = None,
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5,
    json_format: bool = False
) -> None:
    """Set up logging configuration.
    
    Args:
        name: The name of the logger.
        log_level: The logging level. If None, uses the level from settings.
        log_file: Path to the log file. If None, logs only to console.
        max_bytes: Maximum size of the log file before rotation.
        backup_count: Number of backup log files to keep.
        json_format: Whether to use JSON format for logs.
    """
    # Get the root logger
    logger = logging.getLogger(name)
    
    # Clear any existing handlers
    logger.handlers = []
    
    # Set the log level
    if log_level is None:
        log_level = get_log_level()
    logger.setLevel(log_level)
    
    # Create formatters
    if json_format:
        formatter = logging.Formatter(JSON_FORMAT)
    else:
        formatter = logging.Formatter(CONSOLE_FORMAT)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Create file handler if log file is specified
    if log_file:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(log_file)), exist_ok=True)
        
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(log_level)
        file_formatter = logging.Formatter(FILE_FORMAT)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    # Configure third-party loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("telegram").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.getLogger("aiosqlite").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    
    # Log the configuration
    logger.info("Logging configured at level %s", logging.getLevelName(log_level))

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get a logger with the given name.
    
    If logging hasn't been configured yet, it will be configured with default settings.
    
    Args:
        name: The name of the logger. If None, returns the root logger.
        
    Returns:
        logging.Logger: The configured logger instance.
    """
    # Configure logging if not already configured
    if not logging.getLogger().hasHandlers():
        setup_logging()
    
    return logging.getLogger(name)

class RequestIdFilter(logging.Filter):
    """Add request ID to log records."""
    
    def filter(self, record):
        """Add request_id to the log record if it exists in the context."""
        if not hasattr(record, 'request_id'):
            record.request_id = 'N/A'
        return True

class ContextFilter(logging.Filter):
    """Add contextual information to log records."""
    
    def __init__(self, context: Optional[Dict[str, Any]] = None):
        """Initialize the filter with optional context."""
        super().__init__()
        self.context = context or {}
    
    def filter(self, record):
        """Add context to the log record."""
        for key, value in self.context.items():
            setattr(record, key, value)
        return True

def log_execution_time(logger: logging.Logger):
    """Decorator to log the execution time of a function.
    
    Args:
        logger: The logger to use for logging.
        
    Returns:
        callable: The decorated function.
    """
    def decorator(func):
        import time
        from functools import wraps
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                end_time = time.time()
                execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
                logger.debug(
                    "%s executed in %.2f ms",
                    func.__qualname__,
                    execution_time
                )
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                end_time = time.time()
                execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
                logger.debug(
                    "%s executed in %.2f ms",
                    func.__qualname__,
                    execution_time
                )
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else wrapper
    
    return decorator

# Set up default logging when the module is imported
setup_logging()

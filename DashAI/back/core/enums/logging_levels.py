"""Enumeration for logging levels."""
from enum import Enum


class LoggingLevel(str, Enum):
    """Enumeration for logging levels."""

    NOTSET = "NOTSET"
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

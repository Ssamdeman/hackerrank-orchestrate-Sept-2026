"""Filters and formatters for structured observability logging."""

from __future__ import annotations

import logging
from .context import ASSERTION, REQUEST_ID, STAGE



class ContextFilter(logging.Filter):
    """Filter that injects stage, request_id, and assertion into LogRecord."""

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "stage"):
            record.stage = STAGE.get()
        if not hasattr(record, "request_id"):
            record.request_id = REQUEST_ID.get()
        if not hasattr(record, "assertion"):
            record.assertion = ASSERTION.get()
        return True


class ExactLevelFilter(logging.Filter):
    """Filter that only permits records matching an exact log level."""

    def __init__(self, level: int) -> None:
        super().__init__()
        self.level = level

    def filter(self, record: logging.LogRecord) -> bool:
        return record.levelno == self.level


class MinLevelFilter(logging.Filter):
    """Filter that permits records at or above a minimum log level."""

    def __init__(self, min_level: int) -> None:
        super().__init__()
        self.min_level = min_level

    def filter(self, record: logging.LogRecord) -> bool:
        return record.levelno >= self.min_level


class ContextFormatter(logging.Formatter):
    """Formatter that outputs the structured context header on line 1, followed by the message."""

    def __init__(self, datefmt: str | None = None) -> None:
        super().__init__(fmt="%(message)s", datefmt=datefmt)

    def format(self, record: logging.LogRecord) -> str:
        stage = getattr(record, "stage", "unknown")
        request_id = getattr(record, "request_id", "none")
        assertion = getattr(record, "assertion", "")

        parts = [f"stage={stage}", f"request_id={request_id}"]
        if assertion:
            parts.append(f"assertion={assertion}")
        header = " ".join(parts)

        message = super().format(record)
        return f"{header}\n{message}"

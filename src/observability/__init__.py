"""Observability package for deterministic, structured logging."""

from __future__ import annotations

import logging
from .context import (
    ASSERTION,
    REQUEST_ID,
    STAGE,
    bind_context,
    reset_assertion,
    reset_request_id,
    reset_stage,
    set_assertion,
    set_request_id,
    set_stage,
)
from .setup import init_logging, resolve_latest_run_dir



def get_logger(name: str) -> logging.Logger:
    """Get a named logger."""
    return logging.getLogger(name)


__all__ = [
    "ASSERTION",
    "REQUEST_ID",
    "STAGE",
    "bind_context",
    "get_logger",
    "init_logging",
    "reset_assertion",
    "reset_request_id",
    "reset_stage",
    "resolve_latest_run_dir",
    "set_assertion",
    "set_request_id",
    "set_stage",
]

"""Context variables for observability.

Tracks STAGE, REQUEST_ID, and ASSERTION without threading through signatures
or using mutable global state that could bleed between records.
"""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from contextvars import ContextVar, Token

STAGE: ContextVar[str] = ContextVar("stage", default="unknown")
REQUEST_ID: ContextVar[str] = ContextVar("request_id", default="none")
ASSERTION: ContextVar[str] = ContextVar("assertion", default="")


def set_stage(stage: str) -> Token[str]:
    """Set the current pipeline stage context."""
    return STAGE.set(stage)


def reset_stage(token: Token[str]) -> None:
    """Reset STAGE to its prior value using a Token."""
    STAGE.reset(token)


def set_request_id(request_id: str) -> Token[str]:
    """Set the current request_id context."""
    return REQUEST_ID.set(request_id)


def reset_request_id(token: Token[str]) -> None:
    """Reset REQUEST_ID to its prior value using a Token."""
    REQUEST_ID.reset(token)


def set_assertion(assertion: str | int) -> Token[str]:
    """Set the current contract assertion identifier."""
    return ASSERTION.set(str(assertion))


def reset_assertion(token: Token[str]) -> None:
    """Reset ASSERTION to its prior value using a Token."""
    ASSERTION.reset(token)


@contextmanager
def bind_context(
    stage: str | None = None,
    request_id: str | None = None,
    assertion: str | int | None = None,
) -> Generator[None, None, None]:
    """Context manager to bind context variables for a scoped block."""
    tokens: list[tuple[ContextVar[str], Token[str]]] = []
    if stage is not None:
        tokens.append((STAGE, STAGE.set(stage)))
    if request_id is not None:
        tokens.append((REQUEST_ID, REQUEST_ID.set(request_id)))
    if assertion is not None:
        tokens.append((ASSERTION, ASSERTION.set(str(assertion))))

    try:
        yield
    finally:
        for var, token in reversed(tokens):
            var.reset(token)

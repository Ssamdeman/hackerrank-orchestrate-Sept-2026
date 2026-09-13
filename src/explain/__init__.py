"""Explanation generation package."""

from explain.formatting import (
    format_explanation_amount,
    format_explanation_date,
    format_plan_amount,
)

from explain.templates import (
    build_spending_change_phrase,
    render_decision_explanation,
)

__all__ = [
    "build_spending_change_phrase",
    "format_explanation_amount",
    "format_explanation_date",
    "format_plan_amount",
    "render_decision_explanation",
]

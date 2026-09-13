"""src/planner — Candidate generation, spending change enumeration, and ranking engine.
"""

from __future__ import annotations

from planner.candidates import format_payment_plan, generate_candidates
from planner.ranking import (
    determine_affordability_status,
    filter_candidates,
    rank_key,
    select_best_candidate,
)
from planner.spending import (
    enumerate_viable_spending_combinations,
    format_plan_amount,
    format_spending_changes,
)

__all__ = [
    "format_plan_amount",
    "format_payment_plan",
    "generate_candidates",
    "enumerate_viable_spending_combinations",
    "format_spending_changes",
    "filter_candidates",
    "rank_key",
    "select_best_candidate",
    "determine_affordability_status",
]

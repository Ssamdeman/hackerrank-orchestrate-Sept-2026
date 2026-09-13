"""src/planner/ranking.py — Candidate filtering, sort-key ranking, and recommendation selection.

Per docs/architecture.md §4.9 and docs/decision-contract.md §6, §9:
The six-level comparator as a sort key tuple, not a conditional chain:
  1 completes by desired_completion_date
  2 requires no spending changes
  3 minimizes total paid
  4 starts earlier
  5 fewer payments
  6 lowest payment_option_id, compared on NUMERIC SUFFIX

No eligible survivor -> not_recommended.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Sequence

from models import (
    AffordabilityStatus,
    Candidate,
    FinancialProfile,
    PaymentMethod,
    Request,
)
from verify.safety import UserContext, is_safe


def rank_key(
    candidate: Candidate,
    desired_completion_date: date,
    requested_amount: Decimal,
) -> tuple[int, int, Decimal, date, int, int, int]:
    """Compute the six-level comparator sort key tuple.

    1. completes by desired_completion_date (0=yes, 1=no)
    2. requires no spending changes (0=none, 1=has changes)
    3. minimizes total paid (Decimal)
    4. starts earlier (date)
    5. fewer payments (int count)
    6. lowest payment_option_id, compared on NUMERIC SUFFIX (int)
    7. tie-breaker: fewer spending changes (int count)
    """
    completion_date = max(p.date for p in candidate.payments) if candidate.payments else date.max
    completes_by_deadline = (
        bool(candidate.payments)
        and completion_date <= desired_completion_date
        and candidate.total_paid >= requested_amount
    )
    k1 = 0 if completes_by_deadline else 1
    k2 = 1 if candidate.spending_changes else 0
    k3 = candidate.total_paid
    start_date = min(p.date for p in candidate.payments) if candidate.payments else date.max
    k4 = start_date
    k5 = len(candidate.payments)
    if candidate.payment_option_id is not None:
        try:
            k6 = int(candidate.payment_option_id.split("_")[-1])
        except ValueError:
            k6 = 999999
    else:
        k6 = -1
    k7 = len(candidate.spending_changes)
    return (k1, k2, k3, k4, k5, k6, k7)


def filter_candidates(
    candidates: Sequence[Candidate],
    request: Request,
    profile: FinancialProfile,
    context: UserContext,
) -> list[Candidate]:
    """Discard any candidate that fails an eligibility gate (§6.1) or the safety test (§2)."""
    survivors: list[Candidate] = []

    for cand in candidates:
        if cand.method == PaymentMethod.NOT_RECOMMENDED:
            continue

        # Method preference consideration gates
        if cand.method in (PaymentMethod.FULL_PAYMENT, PaymentMethod.WAIT):
            if PaymentMethod.FULL_PAYMENT not in profile.payment_methods_user_will_consider:
                continue
        elif cand.method == PaymentMethod.INSTALLMENTS:
            if PaymentMethod.INSTALLMENTS not in profile.payment_methods_user_will_consider:
                continue
            if (
                profile.max_installment_months is None
                or len(cand.payments) > profile.max_installment_months
            ):
                continue
        elif cand.method == PaymentMethod.PARTIAL_PAYMENT:
            if PaymentMethod.PARTIAL_PAYMENT not in profile.payment_methods_user_will_consider:
                continue

        # Contract §2 & Assertion 14: Must complete on or before desired_completion_date
        completion_date = max(p.date for p in cand.payments) if cand.payments else date.max
        if completion_date > request.desired_completion_date:
            continue

        # Safety test
        safety_res = is_safe(cand, context)
        if not safety_res.is_safe:
            continue

        survivors.append(cand)

    return survivors


def select_best_candidate(
    candidates: Sequence[Candidate],
    request: Request,
    profile: FinancialProfile,
    context: UserContext,
) -> Candidate:
    """Filter candidate pool and select the winning candidate under the 6-level comparator."""
    survivors = filter_candidates(candidates, request, profile, context)
    if not survivors:
        return Candidate(
            method=PaymentMethod.NOT_RECOMMENDED,
            payments=(),
            spending_changes=(),
            payment_option_id=None,
            total_paid=Decimal("0"),
        )

    survivors.sort(
        key=lambda c: rank_key(
            candidate=c,
            desired_completion_date=request.desired_completion_date,
            requested_amount=request.requested_amount,
        )
    )
    return survivors[0]


def determine_affordability_status(
    candidate: Candidate,
) -> AffordabilityStatus:
    """Determine AffordabilityStatus from the winning candidate per §6.2."""
    if candidate.method == PaymentMethod.NOT_RECOMMENDED:
        return AffordabilityStatus.NOT_AFFORDABLE
    if candidate.method == PaymentMethod.FULL_PAYMENT:
        if not candidate.spending_changes:
            return AffordabilityStatus.AFFORDABLE_NOW
        return AffordabilityStatus.AFFORDABLE_WITH_PLAN
    if candidate.method in (PaymentMethod.PARTIAL_PAYMENT, PaymentMethod.INSTALLMENTS):
        return AffordabilityStatus.AFFORDABLE_WITH_PLAN
    if candidate.method == PaymentMethod.WAIT:
        return AffordabilityStatus.AFFORDABLE_LATER
    raise ValueError(f"Unhandled candidate method: {candidate.method}")

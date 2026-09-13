"""Decision explanation generator using deterministic string templates.

Governed by docs/decision_contract.md §11.
Templates are pure deterministic string builders with zero language model calls.
{FLOOR} and {MIN} are both minimum_balance_to_keep (§11.2).
"""

from __future__ import annotations

from decimal import Decimal
from typing import Sequence

from explain.formatting import format_explanation_amount, format_explanation_date
from models import (
    AffordabilityStatus,
    Candidate,
    FinancialEvent,
    PaymentMethod,
    Request,
)
from verify.safety import UserContext


def build_spending_change_phrase(
    candidate: Candidate,
    context: UserContext,
    events_by_id: dict[str, FinancialEvent],
) -> str:
    """Build natural language change phrase from event descriptions (§11.2 T2).

    Example:
      'Stop the family streaming plan'
      'Reduce the weekend food delivery to IDR 665,950'
      'Stop the online backup subscription and reduce the streaming subscription to USD 23.50'
    """
    phrases: list[str] = []
    for sc in candidate.spending_changes:
        ev = events_by_id.get(sc.event_id)
        desc = ev.description.strip() if ev is not None else sc.event_id
        desc_lower = desc.lower()

        if sc.action == "stop":
            phrases.append(f"stop the {desc_lower}")
        elif sc.action == "reduce_to":
            target_amt = sc.target_amount
            if target_amt is None and ev is not None:
                target_amt = ev.minimum_allowed_amount
            if target_amt is None:
                raise ValueError(
                    f"Spending change reduce_to on {sc.event_id} lacks target amount for {context.request_id}"
                )
            amt_str = format_explanation_amount(target_amt, context.home_currency)
            phrases.append(f"reduce the {desc_lower} to {amt_str}")
        else:
            raise ValueError(f"Unknown spending change action {sc.action} for {context.request_id}")

    if not phrases:
        return ""

    full_phrase = " and ".join(phrases)
    return full_phrase[0].upper() + full_phrase[1:]


def render_decision_explanation(
    candidate: Candidate,
    context: UserContext,
    request: Request,
    events: dict[str, FinancialEvent] | Sequence[FinancialEvent],
    safe_amount: Decimal | None = None,
    use_t7_for_not_recommended: bool | None = None,
) -> str:
    """Render deterministic decision explanation for chosen candidate (§11.2).

    Template mapping:
      T1: full_payment / affordable_now (no spending changes)
      T2: full_payment / affordable_with_plan (with spending changes)
      T3: installments / affordable_with_plan
      T4: wait / affordable_later
      T5: partial_payment / affordable_with_plan
      T6: not_recommended / not_affordable (ratio < 0.10 per ASSUMED-16)
      T7: not_recommended / not_affordable (ratio >= 0.10 per ASSUMED-16)
    """
    events_by_id: dict[str, FinancialEvent]
    if isinstance(events, dict):
        events_by_id = events
    else:
        events_by_id = {e.event_id: e for e in events}

    min_str = format_explanation_amount(context.minimum_balance_to_keep, context.home_currency)
    amt_str = format_explanation_amount(context.requested_amount, context.home_currency)

    # T1 & T2: FULL_PAYMENT
    if candidate.method == PaymentMethod.FULL_PAYMENT:
        if candidate.spending_changes:
            # T2 — full_payment with spending changes
            change_phrase = build_spending_change_phrase(candidate, context, events_by_id)
            return f"{change_phrase}, then pay {amt_str} today. This leaves at least {min_str} available."
        else:
            # T1 — full_payment without spending changes (affordable_now)
            return f"Pay {amt_str} today. This leaves at least {min_str} available over the next 90 days."

    # T3: INSTALLMENTS
    if candidate.method == PaymentMethod.INSTALLMENTS:
        num_payments = len(candidate.payments)
        if num_payments == 0:
            raise ValueError(f"Installments candidate has zero payments for {context.request_id}")
        first_payment = candidate.payments[0]
        pmt_str = format_explanation_amount(first_payment.amount, context.home_currency)
        date_str = format_explanation_date(first_payment.date)
        return f"Use {num_payments} installments of {pmt_str}, starting {date_str}. This leaves at least {min_str} available."

    # T4: WAIT
    if candidate.method == PaymentMethod.WAIT:
        if not candidate.payments:
            raise ValueError(f"Wait candidate has zero payments for {context.request_id}")
        pay_date_str = format_explanation_date(candidate.payments[0].date)
        return f"Pay {amt_str} in full on {pay_date_str}. Paying earlier would take the balance below the {min_str} minimum."

    # T5: PARTIAL_PAYMENT
    if candidate.method == PaymentMethod.PARTIAL_PAYMENT:
        if len(candidate.payments) < 2:
            raise ValueError(f"Partial payment candidate has fewer than 2 payments for {context.request_id}")
        p1 = candidate.payments[0]
        p2 = candidate.payments[1]
        amt1_str = format_explanation_amount(p1.amount, context.home_currency)
        amt2_str = format_explanation_amount(p2.amount, context.home_currency)
        p2_date_str = format_explanation_date(p2.date)
        return (
            f"Pay {amt1_str} today and the remaining {amt2_str} on {p2_date_str}. "
            f"This completes the full request and keeps the {min_str} minimum protected."
        )

    # T6 & T7: NOT_RECOMMENDED (ratio >= 0.10 selects T7, else T6 per ASSUMED-16)
    if candidate.method == PaymentMethod.NOT_RECOMMENDED:
        safe = safe_amount if safe_amount is not None else Decimal("0.00")
        if use_t7_for_not_recommended is not None:
            is_t7 = use_t7_for_not_recommended
        else:
            ratio = (safe / context.requested_amount) if context.requested_amount > Decimal("0") else Decimal("0")
            is_t7 = ratio >= Decimal("0.10")

        if is_t7:
            safe_str = format_explanation_amount(safe, context.home_currency)
            return (
                f"Do not proceed with the {amt_str} request. "
                f"Although {safe_str} is available today, the full amount cannot be completed safely within 90 days."
            )
        else:
            desired_date_str = format_explanation_date(request.desired_completion_date)
            return (
                f"Do not make this payment by {desired_date_str}. "
                f"None of the available options keeps the {min_str} minimum protected."
            )

    raise ValueError(f"Unhandled payment method {candidate.method} for {context.request_id}")

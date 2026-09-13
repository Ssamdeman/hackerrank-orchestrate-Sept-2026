"""verify/safety.py — Candidate-aware safety testing and capacity measurement.

Per docs/decision-contract.md §2 and §7.

Provides:
  is_safe(candidate, context) -> SafetyResult
    Evaluates whether a candidate plan violates minimum_balance_to_keep
    on any day across the forecast window.

  compute_amount_safe_to_pay(context) -> Decimal
    Largest payment on request_date passing the safety test,
    before spending changes, capped at requested_amount.
    0.00 is legal and required when opening balance <= minimum_balance_to_keep.

  earliest_date_for_full_payment(context) -> date | None
    First date the full requested_amount passes the safety test.
    Computed WITHOUT optional spending changes.
    Independent of payment-method preferences.
    None when it never becomes safe inside the window.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from typing import Sequence

from forecast.engine import BalanceCurve, project
from models import (
    Amendment,
    Candidate,
    Direction,
    EventStatus,
    FinancialEvent,
    Flow,
    Payment,
    PaymentMethod,
    SpendingChange,
)
from state.fx import FXTable
from state.recurrence import compute_user_burn_rates, resolve_user_recurrence


@dataclass(frozen=True)
class SafetyResult:
    """Result of evaluating a candidate schedule against the safety test."""

    is_safe: bool
    trough: Decimal
    trough_date: date

    @property
    def passed(self) -> bool:
        """Alias for is_safe."""
        return self.is_safe


@dataclass(frozen=True)
class UserContext:
    """Evaluation context for safety testing a user request."""

    user_id: str
    request_date: date
    opening_balance: Decimal
    minimum_balance_to_keep: Decimal
    requested_amount: Decimal
    baseline_flows: tuple[Flow, ...]
    home_currency: str = "USD"
    horizon_days: int = 90
    request_id: str = ""


def build_user_context(
    user_id: str,
    request_date: date,
    opening_balance: Decimal,
    minimum_balance_to_keep: Decimal,
    requested_amount: Decimal,
    events: Sequence[FinancialEvent],
    amendments: Sequence[Amendment] = (),
    home_currency: str | None = None,
    fx_table: FXTable | None = None,
    horizon_days: int = 90,
    request_id: str = "",
) -> UserContext:
    """Construct UserContext with complete baseline cash flows for a user."""
    window_end = request_date + timedelta(days=horizon_days)
    user_events = [e for e in events if e.user_id == user_id]
    curr = home_currency or (user_events[0].currency if user_events else "USD")

    flows: list[Flow] = []

    # 1. Scheduled events and pending debits from historical events
    for e in user_events:
        eff_dt = e.settlement_date if e.settlement_date is not None else e.event_date
        if not (request_date <= eff_dt <= window_end):
            continue
        amt = e.amount
        if fx_table is not None and e.currency != curr:
            amt = fx_table.convert(amt, from_currency=e.currency, to_currency=curr, on_date=eff_dt)
        if e.status == EventStatus.SCHEDULED:
            flows.append(
                Flow(
                    date=eff_dt,
                    amount=amt,
                    direction=e.direction,
                    source_event_id=e.event_id,
                    is_projected=False,
                )
            )
        elif e.status == EventStatus.PENDING and e.direction == Direction.DEBIT:
            flows.append(
                Flow(
                    date=eff_dt,
                    amount=amt,
                    direction=Direction.DEBIT,
                    source_event_id=e.event_id,
                    is_projected=False,
                )
            )

    # 2. Recurring series projections (projections + one-time credits from amendments)
    _, projs = resolve_user_recurrence(
        user_id=user_id,
        events=events,
        amendments=amendments,
        request_date=request_date,
        horizon_days=horizon_days,
        include_burn=False,
        home_currency=curr,
        fx_table=fx_table,
    )
    for occ in projs:
        flows.append(
            Flow(
                date=occ.date,
                amount=occ.amount,
                direction=occ.direction,
                source_event_id=occ.source_event_id,
                is_projected=True,
            )
        )

    # 3. Day-varying daily burn rates across the window (offsets 0 to horizon_days inclusive)
    burn_rates = compute_user_burn_rates(
        user_id=user_id,
        events=events,
        request_date=request_date,
        lookback_days=90,
        home_currency=curr,
        fx_table=fx_table,
    )
    daily_burn = sum((b.daily_burn for b in burn_rates), Decimal("0"))
    if daily_burn > Decimal("0"):
        for day_offset in range(horizon_days + 1):
            dt = request_date + timedelta(days=day_offset)
            flows.append(
                Flow(
                    date=dt,
                    amount=daily_burn,
                    direction=Direction.DEBIT,
                    source_event_id="burn",
                    is_projected=True,
                )
            )

    flows.sort(key=lambda f: f.date)

    return UserContext(
        user_id=user_id,
        request_date=request_date,
        opening_balance=opening_balance,
        minimum_balance_to_keep=minimum_balance_to_keep,
        requested_amount=requested_amount,
        baseline_flows=tuple(flows),
        home_currency=curr,
        horizon_days=horizon_days,
        request_id=request_id,
    )


def is_safe(candidate: Candidate, context: UserContext) -> SafetyResult:
    """Evaluate whether a candidate payment schedule passes the safety test.

    A candidate is safe only when the running balance never falls below
    minimum_balance_to_keep on any day in the window.
    """
    cand_flows = list(context.baseline_flows)

    # Apply candidate spending changes if any
    if candidate.spending_changes:
        stopped_ids: set[str] = set()
        reductions: dict[str, Decimal] = {}
        for sc in candidate.spending_changes:
            if sc.action == "stop":
                stopped_ids.add(sc.event_id)
            elif sc.action == "reduce_to" and sc.target_amount is not None:
                reductions[sc.event_id] = sc.target_amount

        filtered_flows: list[Flow] = []
        for f in cand_flows:
            if f.source_event_id in stopped_ids:
                continue
            if f.source_event_id in reductions:
                filtered_flows.append(
                    Flow(
                        date=f.date,
                        amount=reductions[f.source_event_id],
                        direction=f.direction,
                        source_event_id=f.source_event_id,
                        is_projected=f.is_projected,
                    )
                )
            else:
                filtered_flows.append(f)
        cand_flows = filtered_flows

    # Apply candidate payments as debits
    for p in candidate.payments:
        cand_flows.append(
            Flow(
                date=p.date,
                amount=p.amount,
                direction=Direction.DEBIT,
                source_event_id=f"candidate_payment_{candidate.method.value}",
                is_projected=True,
            )
        )

    curve: BalanceCurve = project(
        opening_balance=context.opening_balance,
        start=context.request_date,
        horizon_days=context.horizon_days,
        flows=cand_flows,
    )

    trough = curve.trough()
    trough_date = curve.trough_date()

    safe = (trough >= context.minimum_balance_to_keep) and (
        context.opening_balance >= context.minimum_balance_to_keep
    )

    return SafetyResult(is_safe=safe, trough=trough, trough_date=trough_date)


def compute_amount_safe_to_pay(context: UserContext) -> Decimal:
    """Largest payment on request_date passing the safety test, before spending changes, capped at requested_amount.

    0.00 is legal and required when the opening balance is at or below minimum_balance_to_keep.
    """
    if context.opening_balance <= context.minimum_balance_to_keep:
        return Decimal("0.00")

    baseline_curve: BalanceCurve = project(
        opening_balance=context.opening_balance,
        start=context.request_date,
        horizon_days=context.horizon_days,
        flows=context.baseline_flows,
    )

    margin = baseline_curve.trough() - context.minimum_balance_to_keep
    return min(context.requested_amount, max(Decimal("0"), margin))


def earliest_date_for_full_payment(context: UserContext) -> date | None:
    """First date the FULL requested_amount passes the safety test.

    Computed WITHOUT optional spending changes. Independent of payment-method
    preferences. Returns None when it never becomes safe inside the window.
    """
    for day_offset in range(context.horizon_days + 1):
        candidate_date = context.request_date + timedelta(days=day_offset)
        cand = Candidate(
            method=PaymentMethod.FULL_PAYMENT,
            payments=(Payment(date=candidate_date, amount=context.requested_amount),),
            spending_changes=(),
            payment_option_id=None,
            total_paid=context.requested_amount,
        )
        res = is_safe(cand, context)
        if res.is_safe:
            return candidate_date
    return None

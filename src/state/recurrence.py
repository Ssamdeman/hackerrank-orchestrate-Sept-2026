"""State module for recurring series detection and calendar-accurate forward projection.

Replaces integer modal-gap-in-days with:
  a) day-stable -> calendar-monthly on the stable day
  b) semi-monthly (2 stable days) -> calendar-monthly on each
  c) day-varying -> flag, do not calendar-project

Computes and projects day-varying burn rate for groceries, transport, dining.
Wires amendments into recurrence in strict precedence order:
  TERMINATE_SERIES -> establish new series -> AMEND_RECURRING_AMOUNT
  -> ADD_RECURRING_EXPENSE -> MARK_NON_RECURRING
  -> ADD_CONFIRMED_INCOME as one-time flows

Minimum 2 occurrences to declare a series (contract §4.4 & directive update).
Pure function, deterministic, zero model calls.
"""

from __future__ import annotations

import calendar
from collections import defaultdict
from dataclasses import dataclass, replace
from datetime import date, timedelta
from decimal import Decimal
from enum import Enum
import logging
from typing import Any, Sequence

from models import (
    AddConfirmedIncome,
    AddRecurringExpense,
    AmendRecurringAmount,
    Amendment,
    Direction,
    EstablishSeries,
    EventStatus,
    EventType,
    FinancialEvent,
    MarkNonRecurring,
    SeriesKey,
    TerminateSeries,
)
from observability import bind_context, init_logging
from state.fx import FXTable


logger = logging.getLogger("state.recurrence")

EXCLUDED_CATEGORIES: frozenset[str] = frozenset({
    "refund",
    "investment_valuation",
    "investment_sale",
    "investment_purchase",
})

EXCLUDED_EVENT_TYPES: frozenset[EventType] = frozenset({
    EventType.REFUND,
    EventType.INVESTMENT_VALUATION,
    EventType.INVESTMENT_SALE,
    EventType.INVESTMENT_PURCHASE,
})

DAY_VARYING_BURN_CATEGORIES: frozenset[str] = frozenset({
    "groceries",
    "transport",
    "dining",
})

GIG_INCOME_DESCRIPTIONS: frozenset[str] = frozenset({
    "Delivery platform payout",
    "Driver platform payout",
    "Task marketplace payout",
    "Weekly app earnings",
})

TERMINATING_PAYROLL_DESCRIPTIONS: frozenset[str] = frozenset({
    "Final employer payroll",
})


class RecurrenceMode(str, Enum):
    """Cadence mode for recurring series forward projection."""
    DAY_STABLE = "day_stable"
    SEMI_MONTHLY = "semi_monthly"
    DAY_VARYING = "day_varying"


@dataclass(frozen=True)
class DetectedSeries:
    """Detected recurring obligation or income stream with cadence mode."""
    key: SeriesKey
    mode: RecurrenceMode
    stable_days: tuple[int, ...]
    latest_amount: Decimal
    occurrences: int
    metadata_event_id: str


@dataclass(frozen=True)
class ProjectedOccurrence:
    """A projected occurrence of a recurring series inside a forward window."""
    date: date
    amount: Decimal
    direction: Direction
    category: str
    description: str
    currency: str
    source_event_id: str


@dataclass(frozen=True)
class DayVaryingBurnRate:
    """Mean daily burn rate for day-varying spend over trailing history."""
    user_id: str
    category: str
    trailing_spend: Decimal
    daily_burn: Decimal
    currency: str
    event_count: int


def detect_series(
    events: Sequence[FinancialEvent],
    min_occurrences: int = 2,
) -> tuple[DetectedSeries, ...]:
    """Detect recurring series from settled historical events across the dataset.

    Groups settled, cash-relevant events by SeriesKey:
    (user_id, direction, category, description, currency).

    Requires at least min_occurrences (default 2) occurrences.
    Categorizes cadence into DAY_STABLE, SEMI_MONTHLY, or DAY_VARYING.
    """
    grouped: dict[SeriesKey, list[FinancialEvent]] = defaultdict(list)

    for ev in events:
        if ev.status != EventStatus.SETTLED:
            continue
        if ev.category in EXCLUDED_CATEGORIES:
            continue
        if ev.event_type in EXCLUDED_EVENT_TYPES:
            continue

        key = SeriesKey(
            user_id=ev.user_id,
            direction=ev.direction,
            category=ev.category,
            description=ev.description,
            currency=ev.currency,
        )
        grouped[key].append(ev)

    detected: list[DetectedSeries] = []

    for key, ev_list in grouped.items():
        if len(ev_list) < min_occurrences:
            continue

        # Sort strictly by event_date
        sorted_evs = sorted(ev_list, key=lambda e: e.event_date)
        dates = [e.event_date for e in sorted_evs]
        unique_days = sorted(set(d.day for d in dates))

        mode: RecurrenceMode
        stable_days: tuple[int, ...]

        if len(unique_days) == 1:
            mode = RecurrenceMode.DAY_STABLE
            stable_days = (unique_days[0],)
        elif len(unique_days) == 2:
            mode = RecurrenceMode.SEMI_MONTHLY
            stable_days = (unique_days[0], unique_days[1])
        else:
            mode = RecurrenceMode.DAY_VARYING
            stable_days = ()

        latest_ev = sorted_evs[-1]

        detected.append(
            DetectedSeries(
                key=key,
                mode=mode,
                stable_days=stable_days,
                latest_amount=latest_ev.amount,
                occurrences=len(sorted_evs),
                metadata_event_id=latest_ev.event_id,
            )
        )

    # Deterministic sort by user_id, category, description
    detected.sort(
        key=lambda s: (
            s.key.user_id,
            s.key.category,
            s.key.description,
            s.key.direction.value,
        )
    )
    return tuple(detected)


def detect_user_series(
    user_id: str,
    events: Sequence[FinancialEvent],
    min_occurrences: int = 2,
) -> tuple[DetectedSeries, ...]:
    """Detect recurring series for a specific user."""
    user_events = [e for e in events if e.user_id == user_id]
    return detect_series(user_events, min_occurrences=min_occurrences)


def project_series(
    series: DetectedSeries,
    start_date: date,
    horizon_days: int = 90,
) -> tuple[ProjectedOccurrence, ...]:
    """Project a detected recurring series across a calendar forward horizon.

    - DAY_STABLE: emits calendar-monthly on the stable day.
    - SEMI_MONTHLY: emits calendar-monthly on each of the 2 stable days.
    - DAY_VARYING: flagged, not calendar-projected (returns empty tuple).
    - BURN CATEGORIES (groceries, transport, dining): NEVER project calendar occurrences.
    """
    if series.key.category in DAY_VARYING_BURN_CATEGORIES:
        return ()

    if series.key.description in GIG_INCOME_DESCRIPTIONS:
        return ()

    if series.key.description in TERMINATING_PAYROLL_DESCRIPTIONS:
        return ()

    if series.mode == RecurrenceMode.DAY_VARYING:
        return ()

    if not series.stable_days:
        return ()

    window_end = start_date + timedelta(days=horizon_days)
    occurrences: list[ProjectedOccurrence] = []

    # Horizon spanning up to ~4 calendar months
    for month_offset in range(0, 5):
        year = start_date.year + (start_date.month - 1 + month_offset) // 12
        month = (start_date.month - 1 + month_offset) % 12 + 1
        max_day = calendar.monthrange(year, month)[1]

        for target_day in series.stable_days:
            clamped_day = min(target_day, max_day)
            occ_date = date(year, month, clamped_day)

            if start_date <= occ_date <= window_end:
                occurrences.append(
                    ProjectedOccurrence(
                        date=occ_date,
                        amount=series.latest_amount,
                        direction=series.key.direction,
                        category=series.key.category,
                        description=series.key.description,
                        currency=series.key.currency,
                        source_event_id=series.metadata_event_id,
                    )
                )

    # Sort occurrences strictly by date
    occurrences.sort(key=lambda o: (o.date, o.description))
    return tuple(occurrences)


def project_user_series(
    series_list: Sequence[DetectedSeries],
    start_date: date,
    horizon_days: int = 90,
) -> tuple[ProjectedOccurrence, ...]:
    """Project all detected recurring series for a user across the horizon."""
    all_projected: list[ProjectedOccurrence] = []
    for s in series_list:
        all_projected.extend(project_series(s, start_date=start_date, horizon_days=horizon_days))
    all_projected.sort(key=lambda o: (o.date, o.description))
    return tuple(all_projected)


def compute_user_burn_rates(
    user_id: str,
    events: Sequence[FinancialEvent],
    request_date: date,
    lookback_days: int = 90,
    home_currency: str | None = None,
    fx_table: FXTable | None = None,
) -> tuple[DayVaryingBurnRate, ...]:
    """Compute trailing spend and mean daily burn for day-varying categories.

    For each (user_id, category) in groceries, transport, dining:
      - sum spend over the lookback_days (default 90) before request_date
      - divide by lookback_days -> mean daily burn
    Uses the user's own trailing history only. No cross-user inference,
    no assumed averages.
    """
    win_start = request_date - timedelta(days=lookback_days)
    burn_rates: list[DayVaryingBurnRate] = []

    user_events = [
        e for e in events
        if e.user_id == user_id
        and e.status == EventStatus.SETTLED
        and e.direction == Direction.DEBIT
        and e.category not in EXCLUDED_CATEGORIES
        and e.event_type not in EXCLUDED_EVENT_TYPES
        and win_start <= e.event_date < request_date
    ]

    home_curr = home_currency or (user_events[0].currency if user_events else "USD")

    for cat in sorted(DAY_VARYING_BURN_CATEGORIES):
        cat_evs = [e for e in user_events if e.category == cat]
        total_spend = Decimal("0")
        for e in cat_evs:
            amt = e.amount
            if fx_table is not None and e.currency != home_curr:
                amt = fx_table.convert(amt, from_currency=e.currency, to_currency=home_curr, on_date=e.event_date)
            total_spend += amt
        count = len(cat_evs)
        curr = home_curr
        daily_burn = total_spend / Decimal(lookback_days) if lookback_days > 0 else Decimal("0")

        burn_rates.append(
            DayVaryingBurnRate(
                user_id=user_id,
                category=cat,
                trailing_spend=total_spend,
                daily_burn=daily_burn,
                currency=curr,
                event_count=count,
            )
        )

    return tuple(burn_rates)


def project_day_varying_burn(
    burn_rates: Sequence[DayVaryingBurnRate],
    start_date: date,
    horizon_days: int = 90,
) -> tuple[ProjectedOccurrence, ...]:
    """Project day-varying daily debit across the forecast window (horizon_days days)."""
    occurrences: list[ProjectedOccurrence] = []
    for offset in range(horizon_days):
        occ_date = start_date + timedelta(days=offset)
        for b in burn_rates:
            if b.daily_burn > Decimal("0"):
                occurrences.append(
                    ProjectedOccurrence(
                        date=occ_date,
                        amount=b.daily_burn,
                        direction=Direction.DEBIT,
                        category=b.category,
                        description=f"Daily {b.category} burn",
                        currency=b.currency,
                        source_event_id=f"burn_{b.user_id}_{b.category}",
                    )
                )
    return tuple(occurrences)


def resolve_user_recurrence(
    user_id: str,
    events: Sequence[FinancialEvent],
    amendments: Sequence[Amendment],
    request_date: date,
    horizon_days: int = 90,
    min_occurrences: int = 2,
    include_burn: bool = True,
    home_currency: str | None = None,
    fx_table: FXTable | None = None,
) -> tuple[tuple[DetectedSeries, ...], tuple[ProjectedOccurrence, ...]]:
    """Apply amendments in strict precedence order and project occurrences.

    Order mandated by architecture:
      TERMINATE_SERIES -> establish new series -> AMEND_RECURRING_AMOUNT
      -> ADD_RECURRING_EXPENSE -> MARK_NON_RECURRING
      -> ADD_CONFIRMED_INCOME as one-time flows

    Asserts that no user ends with a terminated series that is also amended.
    """
    user_events = [e for e in events if e.user_id == user_id]
    user_amends = [a for a in amendments if a.user_id == user_id]

    detected = list(detect_user_series(user_id, user_events, min_occurrences=min_occurrences))

    # 0. Terminate salary series if latest historical salary event indicates employment ended
    historical_salaries = [
        e
        for e in user_events
        if e.category == "salary"
        and (e.settlement_date if e.settlement_date is not None else e.event_date) <= request_date
    ]
    if historical_salaries:
        historical_salaries.sort(
            key=lambda e: (
                e.settlement_date if e.settlement_date is not None else e.event_date,
                e.event_id,
            )
        )
        if historical_salaries[-1].description in TERMINATING_PAYROLL_DESCRIPTIONS:
            detected = [s for s in detected if s.key.category != "salary"]

    # 1. TERMINATE_SERIES
    terminated_keys: set[str] = set()
    terminated_descs: set[str] = set()
    for a in user_amends:
        if isinstance(a, TerminateSeries):
            terminated_keys.add(a.series_key)
            for s in list(detected):
                s_key_str = f"{s.key.user_id}_{s.key.description}_{s.key.currency}"
                if a.series_key in (s_key_str, s.key.description, s.key.category) or (
                    s.key.category == "salary" and "previous employer" in s.key.description.lower()
                ):
                    terminated_descs.add(s.key.description)
                    detected.remove(s)

    # 2. establish new series
    for a in user_amends:
        if isinstance(a, EstablishSeries):
            # Remove any existing detected series with same category + direction to avoid double-projection
            detected = [
                s for s in detected
                if not (s.key.category == a.category and s.key.direction == Direction.CREDIT)
            ]
            new_series = DetectedSeries(
                key=SeriesKey(
                    user_id=user_id,
                    direction=Direction.CREDIT,
                    category=a.category,
                    description=a.description,
                    currency=a.currency,
                ),
                mode=RecurrenceMode.DAY_STABLE,
                stable_days=(a.cadence_day,),
                latest_amount=a.amount,
                occurrences=1,
                metadata_event_id=f"msg_{a.message_id}",
            )
            detected.append(new_series)

    # 3. AMEND_RECURRING_AMOUNT
    for a in user_amends:
        if isinstance(a, AmendRecurringAmount):
            assert a.series_key not in terminated_keys, (
                f"User {user_id} has both TERMINATE_SERIES and AMEND_RECURRING_AMOUNT on series_key {a.series_key}"
            )
            for td in terminated_descs:
                assert td.lower() not in a.series_key.lower(), (
                    f"User {user_id} has both TERMINATE_SERIES and AMEND_RECURRING_AMOUNT on series {td}"
                )
            for idx, s in enumerate(detected):
                s_key_str = f"{s.key.user_id}_{s.key.description}_{s.key.currency}"
                if a.series_key in (s_key_str, s.key.description) or (
                    s.key.category == "salary" and "payroll" in s.key.description.lower()
                ):
                    detected[idx] = replace(s, latest_amount=a.new_amount)
                    break

    # 4. ADD_RECURRING_EXPENSE
    for a in user_amends:
        if isinstance(a, AddRecurringExpense):
            if a.amount is not None and a.amount > Decimal("0"):
                detected.append(
                    DetectedSeries(
                        key=SeriesKey(
                            user_id=user_id,
                            direction=Direction.DEBIT,
                            category=a.category,
                            description=f"Recurring {a.category} from {a.message_id}",
                            currency=a.currency,
                        ),
                        mode=RecurrenceMode.DAY_STABLE,
                        stable_days=(a.start_date.day,),
                        latest_amount=a.amount,
                        occurrences=1,
                        metadata_event_id=f"msg_{a.message_id}",
                    )
                )

    # 5. MARK_NON_RECURRING
    for a in user_amends:
        if isinstance(a, MarkNonRecurring):
            for s in list(detected):
                if s.metadata_event_id == a.event_id and s.occurrences <= 1:
                    detected.remove(s)

    # 6. ADD_CONFIRMED_INCOME as one-time flows
    window_end = request_date + timedelta(days=horizon_days)
    one_time_flows: list[ProjectedOccurrence] = []
    for a in user_amends:
        if isinstance(a, AddConfirmedIncome):
            if request_date <= a.date <= window_end:
                one_time_flows.append(
                    ProjectedOccurrence(
                        date=a.date,
                        amount=a.amount,
                        direction=Direction.CREDIT,
                        category="salary",
                        description=f"Confirmed income from {a.message_id}",
                        currency=a.currency,
                        source_event_id=f"msg_{a.message_id}",
                    )
                )

    recurring_projections = list(project_user_series(detected, start_date=request_date, horizon_days=horizon_days))

    # Deduplicate: drop one-time credits on dates already covered by a recurring salary credit
    recurring_salary_dates: set[date] = {
        occ.date
        for occ in recurring_projections
        if occ.direction == Direction.CREDIT and occ.category == "salary"
    }
    one_time_flows = [
        occ for occ in one_time_flows
        if occ.date not in recurring_salary_dates
    ]

    all_projections = recurring_projections + one_time_flows

    if fx_table is not None and home_currency is not None:
        converted_projections: list[ProjectedOccurrence] = []
        for occ in all_projections:
            if occ.currency != home_currency:
                conv_amt = fx_table.convert(
                    amount=occ.amount,
                    from_currency=occ.currency,
                    to_currency=home_currency,
                    on_date=occ.date,
                )
                converted_projections.append(
                    replace(occ, amount=conv_amt, currency=home_currency)
                )
            else:
                converted_projections.append(occ)
        all_projections = converted_projections

    if include_burn:
        burn_rates = compute_user_burn_rates(
            user_id,
            events,
            request_date=request_date,
            lookback_days=90,
            home_currency=home_currency,
            fx_table=fx_table,
        )
        burn_projections = project_day_varying_burn(burn_rates, start_date=request_date, horizon_days=horizon_days)
        all_projections.extend(burn_projections)

    all_projections.sort(key=lambda o: (o.date, o.description))
    return tuple(detected), tuple(all_projections)


def build_user_recurrence_diagnostic(
    user_id: str,
    events: Sequence[FinancialEvent],
    request_date: date,
    amendments: Sequence[Amendment] = (),
    horizon_days: int = 90,
    min_occurrences: int = 2,
    include_burn: bool = True,
) -> dict[str, Any]:
    """Generate diagnostic structure for a single user's recurring series and projections."""
    detected, projs = resolve_user_recurrence(
        user_id=user_id,
        events=events,
        amendments=amendments,
        request_date=request_date,
        horizon_days=horizon_days,
        min_occurrences=min_occurrences,
        include_burn=include_burn,
    )

    burn_rates = compute_user_burn_rates(user_id, events, request_date=request_date, lookback_days=90)
    total_burn_rate = sum((b.daily_burn for b in burn_rates), Decimal("0"))
    total_trailing_burn_spend = sum((b.trailing_spend for b in burn_rates), Decimal("0"))
    total_projected_burn_outflow = total_burn_rate * Decimal(horizon_days)

    series_diag: list[dict[str, Any]] = []
    for s in detected:
        projected = project_series(s, start_date=request_date, horizon_days=horizon_days)
        series_diag.append({
            "description": s.key.description,
            "category": s.key.category,
            "direction": s.key.direction.value,
            "currency": s.key.currency,
            "mode": s.mode.value,
            "stable_days": list(s.stable_days),
            "occurrences": s.occurrences,
            "latest_amount": str(s.latest_amount),
            "projected_count": len(projected),
            "projected_dates": [o.date.isoformat() for o in projected],
            "projected_amounts": [str(o.amount) for o in projected],
        })

    burn_diag: list[dict[str, Any]] = []
    for b in burn_rates:
        burn_diag.append({
            "category": b.category,
            "currency": b.currency,
            "event_count": b.event_count,
            "trailing_spend": str(b.trailing_spend),
            "daily_burn": str(b.daily_burn),
            "projected_window_outflow": str(b.daily_burn * Decimal(horizon_days)),
        })

    return {
        "user_id": user_id,
        "request_date": request_date.isoformat(),
        "window_end": (request_date + timedelta(days=horizon_days)).isoformat(),
        "total_series": len(detected),
        "day_stable_series": sum(1 for s in detected if s.mode == RecurrenceMode.DAY_STABLE),
        "semi_monthly_series": sum(1 for s in detected if s.mode == RecurrenceMode.SEMI_MONTHLY),
        "day_varying_series": sum(1 for s in detected if s.mode == RecurrenceMode.DAY_VARYING),
        "total_projected_events": len(projs),
        "total_daily_burn": str(total_burn_rate),
        "total_trailing_burn_spend": str(total_trailing_burn_spend),
        "total_projected_burn_outflow": str(total_projected_burn_outflow),
        "burn_rates": burn_diag,
        "series": series_diag,
    }


@dataclass(frozen=True)
class TroughComparison:
    """Trough comparison of running balance curve with vs without day-varying burn."""
    user_id: str
    currency: str
    opening_balance: Decimal
    minimum_balance_to_keep: Decimal
    daily_burn_rate: Decimal
    trough_without_burn: Decimal
    trough_without_burn_date: date
    trough_with_burn: Decimal
    trough_with_burn_date: date
    trough_shift: Decimal


def compute_user_trough_comparison(
    user_id: str,
    opening_balance: Decimal,
    minimum_balance_to_keep: Decimal,
    events: Sequence[FinancialEvent],
    amendments: Sequence[Amendment],
    request_date: date,
    horizon_days: int = 90,
    home_currency: str | None = None,
    fx_table: FXTable | None = None,
) -> TroughComparison:
    """Compute the daily balance curve and trough with vs without day-varying burn applied."""
    window_end = request_date + timedelta(days=horizon_days)

    user_events = [e for e in events if e.user_id == user_id]
    curr = home_currency or (user_events[0].currency if user_events else "USD")

    burn_rates = compute_user_burn_rates(
        user_id=user_id,
        events=events,
        request_date=request_date,
        lookback_days=90,
        home_currency=curr,
        fx_table=fx_table,
    )
    daily_burn = sum((b.daily_burn for b in burn_rates), Decimal("0"))

    daily_flows_without_burn: dict[date, Decimal] = defaultdict(Decimal)
    for e in user_events:
        eff_dt = e.settlement_date if e.settlement_date is not None else e.event_date
        if not (request_date <= eff_dt <= window_end):
            continue
        if e.status == EventStatus.SCHEDULED:
            amt = e.amount
            if fx_table is not None and e.currency != curr:
                amt = fx_table.convert(amt, from_currency=e.currency, to_currency=curr, on_date=eff_dt)
            if e.direction == Direction.DEBIT:
                daily_flows_without_burn[eff_dt] -= amt
            elif e.direction == Direction.CREDIT:
                daily_flows_without_burn[eff_dt] += amt
        elif e.status == EventStatus.PENDING and e.direction == Direction.DEBIT:
            amt = e.amount
            if fx_table is not None and e.currency != curr:
                amt = fx_table.convert(amt, from_currency=e.currency, to_currency=curr, on_date=eff_dt)
            daily_flows_without_burn[eff_dt] -= amt

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
        if occ.direction == Direction.CREDIT:
            daily_flows_without_burn[occ.date] += occ.amount
        else:
            daily_flows_without_burn[occ.date] -= occ.amount

    from forecast.engine import project
    from models import Flow

    flows_no_burn: list[Flow] = []
    for d, net_amt in daily_flows_without_burn.items():
        if net_amt > Decimal("0"):
            flows_no_burn.append(Flow(date=d, amount=net_amt, direction=Direction.CREDIT, source_event_id=None, is_projected=False))
        elif net_amt < Decimal("0"):
            flows_no_burn.append(Flow(date=d, amount=-net_amt, direction=Direction.DEBIT, source_event_id=None, is_projected=False))

    curve_no_burn = project(opening_balance, request_date, horizon_days, flows_no_burn)

    flows_with_burn = list(flows_no_burn)
    if daily_burn > Decimal("0"):
        for day_offset in range(horizon_days + 1):
            dt = request_date + timedelta(days=day_offset)
            flows_with_burn.append(
                Flow(date=dt, amount=daily_burn, direction=Direction.DEBIT, source_event_id="burn", is_projected=True)
            )

    curve_with_burn = project(opening_balance, request_date, horizon_days, flows_with_burn)

    trough_no_burn = curve_no_burn.trough()
    trough_no_burn_date = curve_no_burn.trough_date()
    trough_with_burn = curve_with_burn.trough()
    trough_with_burn_date = curve_with_burn.trough_date()

    shift = trough_with_burn - trough_no_burn
    return TroughComparison(
        user_id=user_id,
        currency=curr,
        opening_balance=opening_balance,
        minimum_balance_to_keep=minimum_balance_to_keep,
        daily_burn_rate=daily_burn,
        trough_without_burn=trough_no_burn,
        trough_without_burn_date=trough_no_burn_date,
        trough_with_burn=trough_with_burn,
        trough_with_burn_date=trough_with_burn_date,
        trough_shift=shift,
    )


def compute_amount_safe_to_pay(
    opening_balance: Decimal,
    minimum_balance_to_keep: Decimal,
    requested_amount: Decimal,
    trough_balance: Decimal,
) -> Decimal:
    """Legacy helper for scripts; canonical module is verify.safety.compute_amount_safe_to_pay(context)."""
    margin = trough_balance - minimum_balance_to_keep
    return min(requested_amount, max(Decimal("0"), margin))

"""src/planner/spending.py — Enumeration and formatting of legal spending changes.

Per docs/decision-contract.md §8:
- Recurring expenses only (from detected recurring series).
- Controllability (flexibility) permits the operation:
  - stop: stoppable or reducible_or_stoppable
  - reduce_to: reducible or reducible_or_stoppable
- Category in user's willingness list:
  - stop: expense_categories_user_is_willing_to_stop
  - reduce_to: expense_categories_user_is_willing_to_reduce
- Category NOT in expense_categories_to_protect.
- stop and reduce_to never target the same event_id.
- reduce_to target amount is always minimum_allowed_amount.
- Cited event_id is the latest metadata-bearing occurrence as of request_date.
- Max 3 spending changes per combination.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Sequence

from models import (
    Direction,
    EventStatus,
    FinancialEvent,
    FinancialProfile,
    Flexibility,
    SpendingChange,
)
from state.recurrence import detect_user_series


def format_plan_amount(amt: Decimal) -> str:
    """Format an amount under decision-contract §7.1 numeric rules.

    Whole numbers render bare without decimal point;
    non-whole numbers render with exactly two decimals.
    """
    if amt == amt.to_integral_value():
        return str(int(amt))
    return f"{amt:.2f}"


def format_spending_changes(changes: Sequence[SpendingChange]) -> str:
    """Format a collection of spending changes into the contract §8.1 grammar.

    'none' when no changes are present.
    Multiple changes are separated by '|' and sorted deterministically
    by the numeric suffix of event_id.
    """
    if not changes:
        return "none"

    def _sort_key(sc: SpendingChange) -> int:
        try:
            return int(sc.event_id.split("_")[-1])
        except ValueError:
            return 999999

    sorted_changes = sorted(changes, key=_sort_key)
    parts: list[str] = []
    for sc in sorted_changes:
        if sc.action == "stop":
            parts.append(f"stop:{sc.event_id}")
        elif sc.action == "reduce_to":
            assert sc.target_amount is not None, f"reduce_to on {sc.event_id} missing target_amount"
            amt_str = format_plan_amount(sc.target_amount)
            parts.append(f"reduce_to:{sc.event_id}:{amt_str}")
        else:
            raise ValueError(f"Unknown spending change action: {sc.action}")
    return "|".join(parts)


def enumerate_viable_spending_combinations(
    user_id: str,
    request_date: date,
    profile: FinancialProfile,
    events: Sequence[FinancialEvent],
    max_changes: int = 3,
) -> tuple[tuple[SpendingChange, ...], ...]:
    """Enumerate legal spending-change combinations (up to max_changes, default 3).

    Applies the gate chain in strict order:
      1. Event is recurring (from detected recurring series).
      2. Category NOT in expense_categories_to_protect.
      3. For 'stop': category in user's willingness list and flexibility permits.
      4. For 'reduce_to': category in user's willingness list, flexibility permits,
         and minimum_allowed_amount is non-null.
      5. Cited event_id is the latest metadata-bearing occurrence as of request_date.
      6. In combinations, stop and reduce_to never target the same event_id.
    """
    user_events = [
        e
        for e in events
        if e.user_id == user_id
        and (e.settlement_date if e.settlement_date is not None else e.event_date) <= request_date
    ]

    series_list = detect_user_series(user_id, user_events, min_occurrences=2)
    debit_series = [ser for ser in series_list if ser.key.direction == Direction.DEBIT]

    single_changes: list[SpendingChange] = []

    for ser in debit_series:
        cat = ser.key.category
        if cat in profile.expense_categories_to_protect:
            continue

        s_evs = [
            e
            for e in user_events
            if e.category == ser.key.category
            and e.description == ser.key.description
            and e.direction == Direction.DEBIT
            and e.status == EventStatus.SETTLED
        ]
        s_evs.sort(
            key=lambda e: (
                e.settlement_date if e.settlement_date is not None else e.event_date,
                e.event_date,
                e.event_id,
            )
        )

        # Stop check
        if cat in profile.expense_categories_user_is_willing_to_stop:
            meta_stop = [
                e
                for e in s_evs
                if e.flexibility in (Flexibility.STOPPABLE, Flexibility.REDUCIBLE_OR_STOPPABLE)
            ]
            if meta_stop:
                latest_stop_ev = meta_stop[-1]
                single_changes.append(
                    SpendingChange(
                        event_id=latest_stop_ev.event_id,
                        action="stop",
                        target_amount=None,
                    )
                )

        # Reduce_to check
        if cat in profile.expense_categories_user_is_willing_to_reduce:
            meta_red = [
                e
                for e in s_evs
                if e.flexibility in (Flexibility.REDUCIBLE, Flexibility.REDUCIBLE_OR_STOPPABLE)
                and e.minimum_allowed_amount is not None
            ]
            if meta_red:
                latest_red_ev = meta_red[-1]
                assert latest_red_ev.minimum_allowed_amount is not None
                single_changes.append(
                    SpendingChange(
                        event_id=latest_red_ev.event_id,
                        action="reduce_to",
                        target_amount=latest_red_ev.minimum_allowed_amount,
                    )
                )

    combinations: list[tuple[SpendingChange, ...]] = []

    # Size 1
    for sc in single_changes:
        combinations.append((sc,))

    # Size 2
    if max_changes >= 2:
        n = len(single_changes)
        for i in range(n):
            for j in range(i + 1, n):
                sc1, sc2 = single_changes[i], single_changes[j]
                if sc1.event_id != sc2.event_id:
                    combinations.append((sc1, sc2))

    # Size 3
    if max_changes >= 3:
        n = len(single_changes)
        for i in range(n):
            for j in range(i + 1, n):
                for k in range(j + 1, n):
                    sc1, sc2, sc3 = single_changes[i], single_changes[j], single_changes[k]
                    if len({sc1.event_id, sc2.event_id, sc3.event_id}) == 3:
                        combinations.append((sc1, sc2, sc3))

    return tuple(combinations)

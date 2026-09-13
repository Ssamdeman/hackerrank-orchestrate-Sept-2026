"""State module for loading and applying typed message amendments.

Applies the closed amendment set from decision_contract.md §10.2:
- AMEND_AMOUNT(event_id, new_amount)
- CANCEL_EVENT(event_id)
- DELAY_EVENT(event_id, new_date)
- CONFIRM_EVENT(event_id)
- ADD_CONFIRMED_INCOME(date, amount, currency)

Conflict precedence (contract §10.1) is resolved here, terminating in the
financially safer interpretation: lower income, higher expense, later credit,
earlier debit.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import date
from decimal import Decimal
import json
import logging
from pathlib import Path
from typing import Any, Sequence

from models import (
    AddConfirmedIncome,
    AddRecurringExpense,
    AmendAmount,
    Amendment,
    AmendmentAction,
    AmendRecurringAmount,
    CancelEvent,
    ConfirmEvent,
    DelayEvent,
    Direction,
    EventStatus,
    EventType,
    EstablishSeries,
    FinancialEvent,
    Flexibility,
    MarkNonRecurring,
    TerminateSeries,
)
from observability import bind_context, init_logging


_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DETERMINISTIC_AMENDMENTS_PATH = _REPO_ROOT / "src" / "data" / "message_amendments.json"
MODEL_AMENDMENTS_PATH = _REPO_ROOT / "src" / "data" / "model_message_amendments.json"
DEFAULT_AMENDMENTS_PATH = MODEL_AMENDMENTS_PATH

logger = logging.getLogger("state.amendments")
ALLOWED_EXPENSE_CATEGORIES: frozenset[str] = frozenset({
    "groceries", "transport", "dining", "salary", "utilities", "rent",
    "cloud_storage", "shopping", "streaming", "debt_repayment", "entertainment",
    "insurance", "music_subscription", "healthcare", "delivery_membership",
    "education", "housing", "gym", "family_support", "investment",
    "work_expense", "windfall",
})


def load_message_amendments(
    json_path: Path | str = DEFAULT_AMENDMENTS_PATH,
) -> tuple[Amendment, ...]:
    """Load frozen offline message amendments from JSON.

    Pure I/O reader. Zero model calls. Validates against closed AmendmentAction
    vocabulary and enforces strict category validation.
    """
    path = Path(json_path)
    if not path.is_file():
        logger.info(
            "stage=offline_perception request_id=none event=amendments_file_missing path=%s",
            path,
        )
        return ()

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError(f"Expected list of amendments in {path}, got {type(data)}")

    amendments: list[Amendment] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        mid = str(item["message_id"])
        uid = str(item["user_id"])
        action_str = str(item["action"])
        src_mid = str(item.get("source_message_id", mid))
        src_sub = str(item.get("source_substring", ""))
        tmpl_id = str(item.get("template_id", ""))

        if action_str == AmendmentAction.AMEND_AMOUNT.value:
            eid = str(item["event_id"])
            amt = Decimal(str(item["new_amount"]))
            amendments.append(
                AmendAmount(
                    event_id=eid,
                    new_amount=amt,
                    message_id=mid,
                    user_id=uid,
                    source_message_id=src_mid,
                    source_substring=src_sub,
                    template_id=tmpl_id,
                )
            )
        elif action_str == AmendmentAction.CANCEL_EVENT.value:
            eid = str(item["event_id"])
            amendments.append(
                CancelEvent(
                    event_id=eid,
                    message_id=mid,
                    user_id=uid,
                    source_message_id=src_mid,
                    source_substring=src_sub,
                    template_id=tmpl_id,
                )
            )
        elif action_str == AmendmentAction.DELAY_EVENT.value:
            eid = str(item["event_id"])
            dt = date.fromisoformat(str(item["new_date"]))
            amendments.append(
                DelayEvent(
                    event_id=eid,
                    new_date=dt,
                    message_id=mid,
                    user_id=uid,
                    source_message_id=src_mid,
                    source_substring=src_sub,
                    template_id=tmpl_id,
                )
            )
        elif action_str == AmendmentAction.CONFIRM_EVENT.value:
            eid = str(item["event_id"])
            amendments.append(
                ConfirmEvent(
                    event_id=eid,
                    message_id=mid,
                    user_id=uid,
                    source_message_id=src_mid,
                    source_substring=src_sub,
                    template_id=tmpl_id,
                )
            )
        elif action_str == AmendmentAction.ADD_CONFIRMED_INCOME.value:
            dt = date.fromisoformat(str(item["date"]))
            amt = Decimal(str(item["amount"]))
            curr = str(item["currency"])
            amendments.append(
                AddConfirmedIncome(
                    date=dt,
                    amount=amt,
                    currency=curr,
                    message_id=mid,
                    user_id=uid,
                    source_message_id=src_mid,
                    source_substring=src_sub,
                    template_id=tmpl_id,
                )
            )
        elif action_str == AmendmentAction.AMEND_RECURRING_AMOUNT.value:
            sk = str(item.get("series_key", "salary"))
            amt = Decimal(str(item["new_amount"]))
            eff_dt = date.fromisoformat(str(item["effective_date"]))
            amendments.append(
                AmendRecurringAmount(
                    series_key=sk,
                    new_amount=amt,
                    effective_date=eff_dt,
                    message_id=mid,
                    user_id=uid,
                    source_message_id=src_mid,
                    source_substring=src_sub,
                    template_id=tmpl_id,
                )
            )
        elif action_str == AmendmentAction.TERMINATE_SERIES.value:
            sk = str(item.get("series_key", "salary"))
            fin_dt = date.fromisoformat(str(item["final_date"]))
            amendments.append(
                TerminateSeries(
                    series_key=sk,
                    final_date=fin_dt,
                    message_id=mid,
                    user_id=uid,
                    source_message_id=src_mid,
                    source_substring=src_sub,
                    template_id=tmpl_id,
                )
            )
        elif action_str == AmendmentAction.ADD_RECURRING_EXPENSE.value:
            amt_raw = item.get("amount")
            exp_amt: Decimal | None = Decimal(str(amt_raw)) if amt_raw is not None else None
            curr = str(item["currency"])
            start_dt = date.fromisoformat(str(item["start_date"]))
            cat = str(item.get("category", "family_support"))
            if cat not in ALLOWED_EXPENSE_CATEGORIES and cat != "NEEDS_DECISION":
                raise ValueError(
                    f"Category '{cat}' is not among the 22 schema categories in docs/data-profile.md §5.5"
                )
            amendments.append(
                AddRecurringExpense(
                    user_id=uid,
                    amount=exp_amt,
                    currency=curr,
                    start_date=start_dt,
                    category=cat,
                    message_id=mid,
                    source_message_id=src_mid,
                    source_substring=src_sub,
                    template_id=tmpl_id,
                )
            )
        elif action_str == AmendmentAction.MARK_NON_RECURRING.value:
            eid = str(item["event_id"])
            amendments.append(
                MarkNonRecurring(
                    event_id=eid,
                    message_id=mid,
                    user_id=uid,
                    source_message_id=src_mid,
                    source_substring=src_sub,
                    template_id=tmpl_id,
                )
            )
        elif action_str == AmendmentAction.ESTABLISH_SERIES.value:
            amt = Decimal(str(item["amount"]))
            curr = str(item["currency"])
            start_dt = date.fromisoformat(str(item["start_date"]))
            sk = str(item.get("series_key", "salary"))
            cat = str(item.get("category", "salary"))
            desc = str(item.get("description", "New employer payroll"))
            cday = int(item.get("cadence_day", 15))
            amendments.append(
                EstablishSeries(
                    user_id=uid,
                    amount=amt,
                    currency=curr,
                    start_date=start_dt,
                    series_key=sk,
                    category=cat,
                    description=desc,
                    cadence_day=cday,
                    message_id=mid,
                    source_message_id=src_mid,
                    source_substring=src_sub,
                    template_id=tmpl_id,
                )
            )
        else:
            raise ValueError(
                f"Unknown or illegal amendment action '{action_str}' in {mid}"
            )

    return tuple(amendments)


def apply_amendments(
    events: Sequence[FinancialEvent],
    amendments: Sequence[Amendment],
) -> tuple[FinancialEvent, ...]:
    """Apply typed amendments to financial events with conflict precedence.

    Raises ValueError if an amendment references an event_id not present in events.
    Returns a new tuple of FinancialEvents including updated events and synthesized
    confirmed income events.
    """
    event_map: dict[str, FinancialEvent] = {e.event_id: e for e in events}

    # Group amendments by target event
    event_amendments: dict[str, list[Amendment]] = {}
    new_income_amendments: list[AddConfirmedIncome] = []
    new_expense_amendments: list[AddRecurringExpense] = []

    for amend in amendments:
        if isinstance(amend, AddConfirmedIncome):
            new_income_amendments.append(amend)
        elif isinstance(amend, AddRecurringExpense):
            new_expense_amendments.append(amend)
        elif isinstance(amend, (AmendRecurringAmount, TerminateSeries, EstablishSeries)):
            # Series-level modifications take effect during recurrence forecasting
            pass
        elif isinstance(amend, MarkNonRecurring):
            eid = amend.event_id
            if eid not in event_map:
                raise ValueError(
                    f"Amendment from {amend.message_id} targets non-existent event_id '{eid}'"
                )
            if eid not in event_amendments:
                event_amendments[eid] = []
            event_amendments[eid].append(amend)
        else:
            eid = amend.event_id
            if eid not in event_map:
                raise ValueError(
                    f"Amendment from {amend.message_id} targets non-existent event_id '{eid}'"
                )
            if eid not in event_amendments:
                event_amendments[eid] = []
            event_amendments[eid].append(amend)

    # Apply event-targeted amendments
    updated_events: dict[str, FinancialEvent] = dict(event_map)

    for eid, amend_list in event_amendments.items():
        current_event = updated_events[eid]

        # Resolve conflict precedence (§10.1):
        # 1. Explicit cancellation
        # 2. Amount amendment
        # 3. Delay
        # 4. Confirmation / settlement / non-recurring
        cancels = [a for a in amend_list if isinstance(a, CancelEvent)]
        if cancels:
            current_event = replace(current_event, status=EventStatus.CANCELLED)

        amends = [a for a in amend_list if isinstance(a, AmendAmount)]
        if amends:
            # Safer interpretation for conflicts: lower credit / higher debit (§10.1 rule 4)
            if current_event.direction == Direction.CREDIT:
                target_amount = min(a.new_amount for a in amends)
            else:
                target_amount = max(a.new_amount for a in amends)
            current_event = replace(current_event, amount=target_amount)

        delays = [a for a in amend_list if isinstance(a, DelayEvent)]
        if delays:
            # Safer interpretation: later credit / earlier debit
            if current_event.direction == Direction.CREDIT:
                target_date = max(a.new_date for a in delays)
            else:
                target_date = min(a.new_date for a in delays)
            current_event = replace(
                current_event,
                event_date=target_date,
                settlement_date=target_date if current_event.settlement_date is not None else None,
            )

        confirms = [a for a in amend_list if isinstance(a, ConfirmEvent)]
        if confirms and current_event.status != EventStatus.CANCELLED:
            current_event = replace(current_event, status=EventStatus.SETTLED)

        non_recurrings = [a for a in amend_list if isinstance(a, MarkNonRecurring)]
        if non_recurrings and current_event.status != EventStatus.CANCELLED:
            current_event = replace(current_event, status=EventStatus.SETTLED)

        updated_events[eid] = current_event

    # Synthesize ADD_CONFIRMED_INCOME and ADD_RECURRING_EXPENSE events
    synthesized_events: list[FinancialEvent] = []
    for inc in new_income_amendments:
        synth_id = f"event_msg_{inc.message_id}"
        synthesized_events.append(
            FinancialEvent(
                event_id=synth_id,
                user_id=inc.user_id,
                event_date=inc.date,
                settlement_date=inc.date,
                amount=inc.amount,
                currency=inc.currency,
                direction=Direction.CREDIT,
                category="salary",
                description=f"Confirmed income from {inc.message_id}",
                flexibility=Flexibility.FIXED,
                minimum_allowed_amount=None,
                status=EventStatus.SETTLED,
                linked_event_id=None,
                event_type=EventType.INCOME,
            )
        )

    for exp in new_expense_amendments:
        if exp.amount is not None and exp.amount > 0:
            synth_id = f"event_exp_{exp.message_id}"
            synthesized_events.append(
                FinancialEvent(
                    event_id=synth_id,
                    user_id=exp.user_id,
                    event_date=exp.start_date,
                    settlement_date=exp.start_date,
                    amount=exp.amount,
                    currency=exp.currency,
                    direction=Direction.DEBIT,
                    category=exp.category,
                    description=f"Recurring {exp.category} from {exp.message_id}",
                    flexibility=Flexibility.FIXED,
                    minimum_allowed_amount=None,
                    status=EventStatus.SETTLED,
                    linked_event_id=None,
                    event_type=EventType.EXPENSE,
                )
            )

    # Maintain original event order, append synthesized events
    result: list[FinancialEvent] = []
    for e in events:
        result.append(updated_events[e.event_id])
    result.extend(synthesized_events)

    return tuple(result)


def main() -> None:
    """Self-test demonstrating clean loading and application to dataset."""
    init_logging()
    with bind_context(stage="state_amendments"):
        logger.info("Running state.amendments self-test")
        from dataio.loaders import load_financial_events

        events = load_financial_events()
        amendments = load_message_amendments()

        logger.info("Loaded %d events and %d amendments", len(events), len(amendments))

        updated = apply_amendments(events, amendments)
        logger.info(
            "Amendments applied successfully. Original events: %d, Result events: %d",
            len(events),
            len(updated),
        )
        print(f"Self-test PASSED: {len(amendments)} amendments applied cleanly to {len(events)} events (new total: {len(updated)}).")


if __name__ == "__main__":
    main()

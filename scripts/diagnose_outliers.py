"""Detailed flow ledgers and historical category spend analysis for user_05 and user_10."""

from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
import sys

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SRC_DIR = _REPO_ROOT / "src"
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from dataio.loaders import (
    load_financial_events,
    load_financial_profiles,
    load_sample_requests,
    load_exchange_rates,
)
from state.amendments import load_message_amendments
from state.fx import build_fx_table
from state.recurrence import compute_user_burn_rates, resolve_user_recurrence
from models import Direction, EventStatus


def print_user_analysis(target_user: str, gt_trough: Decimal) -> None:
    events = load_financial_events()
    profiles = load_financial_profiles()
    samples = load_sample_requests()
    amends = load_message_amendments()
    rates = load_exchange_rates()
    fx = build_fx_table(rates)

    sample_req = [s for s in samples if s.user_id == target_user][0]
    prof = profiles[target_user]
    ccy = prof.home_currency
    req_date = sample_req.request_date
    win_start = req_date - timedelta(days=90)
    win_end = req_date + timedelta(days=90)

    print(f"\n{'=' * 35} OUTLIER ANALYSIS: {target_user} ({sample_req.request_id}) {'=' * 35}")
    print(f"Currency: {ccy} | Request Date: {req_date} | Horizon End: {win_end}")
    print(f"Opening Balance:         {prof.current_available_balance:14,.2f} {ccy}")
    print(f"Minimum Balance to Keep: {prof.minimum_balance_to_keep:14,.2f} {ccy}")
    print(f"Requested Amount:        {sample_req.requested_amount:14,.2f} {ccy}")
    print(f"Ground Truth Trough:     {gt_trough:14,.2f} {ccy}")
    print(f"Ground Truth Safe:       {sample_req.amount_safe_to_pay:14,.2f} {ccy}")

    # 1. Trailing 90-day actual spend by category
    trailing_spend: dict[str, Decimal] = defaultdict(Decimal)
    trailing_counts: dict[str, int] = defaultdict(int)
    trailing_inflow: dict[str, Decimal] = defaultdict(Decimal)
    trailing_inflow_counts: dict[str, int] = defaultdict(int)

    for e in events:
        if e.user_id == target_user:
            eff_dt = e.settlement_date if e.settlement_date is not None else e.event_date
            if win_start <= eff_dt < req_date:
                amt = e.amount
                if e.currency != ccy:
                    amt = fx.convert(amt, from_currency=e.currency, to_currency=ccy, on_date=eff_dt)
                if e.direction == Direction.DEBIT:
                    trailing_spend[e.category] += amt
                    trailing_counts[e.category] += 1
                elif e.direction == Direction.CREDIT:
                    trailing_inflow[e.category] += amt
                    trailing_inflow_counts[e.category] += 1

    total_actual_spend = sum(trailing_spend.values(), Decimal("0"))
    total_actual_income = sum(trailing_inflow.values(), Decimal("0"))

    print("\n--- [A] TRAILING 90-DAY ACTUAL SPEND BY CATEGORY ---")
    for cat, amt in sorted(trailing_spend.items(), key=lambda x: -x[1]):
        pct = (amt / total_actual_spend * 100) if total_actual_spend > 0 else Decimal("0")
        cnt = trailing_counts[cat]
        print(f"  {cat:22s}: {amt:14,.2f} {ccy} ({cnt:2d} events, {pct:5.1f}%)")
    print(f"  {'TOTAL OUTFLOW':22s}: {total_actual_spend:14,.2f} {ccy}")

    print("\n--- [B] TRAILING 90-DAY ACTUAL INFLOW BY CATEGORY ---")
    for cat, amt in sorted(trailing_inflow.items(), key=lambda x: -x[1]):
        cnt = trailing_inflow_counts[cat]
        print(f"  {cat:22s}: {amt:14,.2f} {ccy} ({cnt:2d} events)")
    print(f"  {'TOTAL INFLOW':22s}: {total_actual_income:14,.2f} {ccy}")

    # 2. Daily Burn Rates
    burns = compute_user_burn_rates(target_user, events, req_date, 90, ccy, fx)
    daily_burn = sum((b.daily_burn for b in burns), Decimal("0"))
    print("\n--- [C] TRAILING DAY-VARYING BURN RATES ---")
    for b in burns:
        print(f"  {b.category:12s}: trailing={b.trailing_spend:12,.2f} {ccy} | daily={b.daily_burn:10,.2f} {ccy} ({b.event_count} events)")
    print(f"  TOTAL DAILY BURN: {daily_burn:12,.2f} {ccy} (90-day cumulative = {daily_burn * Decimal(90):12,.2f} {ccy})")

    # 3. Forward Projected Flows
    sched_events: list[tuple[date, str, str, Direction, Decimal]] = []
    for e in events:
        if e.user_id == target_user:
            eff_dt = e.settlement_date if e.settlement_date is not None else e.event_date
            if req_date <= eff_dt <= win_end:
                amt = e.amount
                if e.currency != ccy:
                    amt = fx.convert(amt, from_currency=e.currency, to_currency=ccy, on_date=eff_dt)
                if e.status == EventStatus.SCHEDULED:
                    sched_events.append((eff_dt, e.category, f"Scheduled {e.description}", e.direction, amt))
                elif e.status == EventStatus.PENDING and e.direction == Direction.DEBIT:
                    sched_events.append((eff_dt, e.category, f"Pending {e.description}", e.direction, amt))

    _, projs = resolve_user_recurrence(target_user, events, amends, req_date, 90, include_burn=False, home_currency=ccy, fx_table=fx)
    rec_events: list[tuple[date, str, str, Direction, Decimal]] = [
        (occ.date, occ.category, occ.description, occ.direction, occ.amount)
        for occ in projs
    ]

    all_flows: list[tuple[date, str, str, Direction, Decimal]] = sched_events + rec_events
    all_flows.sort(key=lambda x: (x[0], 0 if x[3] == Direction.CREDIT else 1))

    # Flow by date map for running balance
    date_flows: dict[date, list[tuple[str, str, Direction, Decimal]]] = defaultdict(list)
    for dt, cat, desc, direction, amt in all_flows:
        date_flows[dt].append((cat, desc, direction, amt))

    print("\n--- [D] FULL FORWARD FLOW LEDGER (90-DAY HORIZON) ---")
    print(f"{'Date':10s} | {'Category':18s} | {'Description':32s} | {'Amount':14s} | {'Flow':6s} | {'Cumulative Burn':15s} | {'Running Balance':18s}")
    print("-" * 125)

    running_bal = prof.current_available_balance
    cum_burn = Decimal("0")
    trough_val = running_bal
    trough_dt = req_date

    for day_idx in range(91):
        dt = req_date + timedelta(days=day_idx)
        cum_burn += daily_burn
        day_events = date_flows.get(dt, [])

        if not day_events and day_idx % 15 != 0 and day_idx != 90:
            # Check balance drop due to burn alone
            bal_today = running_bal - daily_burn
            running_bal = bal_today
            if running_bal < trough_val:
                trough_val = running_bal
                trough_dt = dt
            continue

        if not day_events:
            running_bal -= daily_burn
            if running_bal < trough_val:
                trough_val = running_bal
                trough_dt = dt
            print(f"{dt.isoformat():10s} | {'(daily burn)':18s} | {'Smoothed day-varying spend':32s} | {-daily_burn:14,.2f} | {'DEBIT':6s} | {cum_burn:15,.2f} | {running_bal:18,.2f}")
            continue

        for cat, desc, direction, amt in day_events:
            running_bal -= daily_burn
            if direction == Direction.CREDIT:
                running_bal += amt
                flow_str = "CREDIT"
                amt_str = f"+{amt:12,.2f}"
            else:
                running_bal -= amt
                flow_str = "DEBIT"
                amt_str = f"-{amt:12,.2f}"

            if running_bal < trough_val:
                trough_val = running_bal
                trough_dt = dt

            print(f"{dt.isoformat():10s} | {cat:18s} | {desc[:32]:32s} | {amt_str:14s} | {flow_str:6s} | {cum_burn:15,.2f} | {running_bal:18,.2f}")

    print("-" * 125)
    print(f"OUR FORECAST TROUGH:     {trough_val:14,.2f} {ccy} on {trough_dt}")
    print(f"GROUND TRUTH TROUGH:     {gt_trough:14,.2f} {ccy}")
    print(f"DISCREPANCY (Ours - GT): {trough_val - gt_trough:14,.2f} {ccy}")


def main() -> None:
    print_user_analysis("user_05", Decimal("13837.00"))
    print_user_analysis("user_10", Decimal("238100.00"))


if __name__ == "__main__":
    main()

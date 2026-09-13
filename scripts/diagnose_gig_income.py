"""Diagnostic script for 31 day-varying credit series (gig income)."""

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
    load_requests,
    load_exchange_rates,
)
from state.amendments import load_message_amendments
from state.fx import build_fx_table
from state.recurrence import (
    compute_user_burn_rates,
    compute_amount_safe_to_pay,
    resolve_user_recurrence,
    detect_series,
    RecurrenceMode,
)
from models import Direction, EventStatus


def main() -> None:
    events = load_financial_events()
    profiles = load_financial_profiles()
    samples = load_sample_requests()
    eval_requests = load_requests()
    amends = load_message_amendments()
    rates = load_exchange_rates()
    fx = build_fx_table(rates)

    detected_all = detect_series(events)
    dv_credits = [
        s for s in detected_all
        if s.key.direction == Direction.CREDIT and s.mode == RecurrenceMode.DAY_VARYING
    ]

    calib_map = {s.user_id: s for s in samples}
    eval_map = {r.user_id: r for r in eval_requests}

    # Group series by user
    user_series_map = defaultdict(list)
    for s in dv_credits:
        user_series_map[s.key.user_id].append(s)

    print("=" * 90)
    print("DAY-VARYING CREDIT SERIES (31 SERIES ACROSS 11 USERS)")
    print("=" * 90)

    for uid in sorted(user_series_map.keys()):
        p = profiles[uid]
        ccy = p.home_currency
        series_list = user_series_map[uid]
        calib_req = calib_map.get(uid)
        eval_req = eval_map.get(uid)
        calib_str = f"{calib_req.request_id} (GT safe = {calib_req.amount_safe_to_pay:,.2f} {ccy})" if calib_req else f"None (touches evaluation row {eval_req.request_id if eval_req else 'N/A'})"

        # Reference date for lookback
        ref_date = calib_req.request_date if calib_req else (eval_req.request_date if eval_req else date(2025, 1, 1))
        win_start = ref_date - timedelta(days=90)

        # Compute trailing 90-day actual income for these specific series
        total_user_gig_income = Decimal("0")

        print(f"\nUser: {uid:8s} | Home Currency: {ccy:4s} | Touches Calibration: {calib_str}")
        print(f"  Reference Date: {ref_date} (Lookback: {win_start} to {ref_date})")

        for s in series_list:
            # Match events in lookback for this series
            evs = [
                e for e in events
                if e.user_id == uid
                and e.category == s.key.category
                and e.description == s.key.description
                and e.status == EventStatus.SETTLED
                and win_start <= e.event_date < ref_date
            ]
            spend = sum((e.amount for e in evs), Decimal("0"))
            daily_rate = spend / Decimal(90)
            total_user_gig_income += spend
            print(
                f"    - Series: '{s.key.description:28s}': trailing_90d={spend:12,.2f} {s.key.currency} "
                f"({len(evs):2d} events) | implied daily rate={daily_rate:10,.2f} {s.key.currency}"
            )

        total_daily_rate = total_user_gig_income / Decimal(90)
        print(f"  TOTAL TRAILING GIG INCOME: {total_user_gig_income:14,.2f} {ccy} | TOTAL DAILY RATE: {total_daily_rate:10,.2f} {ccy}/day")

        # If user touches calibration, simulate smoothing income
        if calib_req:
            req_date = calib_req.request_date
            # Base simulation without smoothing
            burns = compute_user_burn_rates(uid, events, req_date, 90, ccy, fx)
            daily_burn = sum((b.daily_burn for b in burns), Decimal("0"))

            sched_events = []
            for e in events:
                if e.user_id == uid:
                    eff_dt = e.settlement_date if e.settlement_date is not None else e.event_date
                    if req_date <= eff_dt <= req_date + timedelta(days=90):
                        amt = e.amount
                        if e.currency != ccy:
                            amt = fx.convert(amt, from_currency=e.currency, to_currency=ccy, on_date=eff_dt)
                        if e.status == EventStatus.SCHEDULED:
                            sched_events.append((eff_dt, e.direction, amt))
                        elif e.status == EventStatus.PENDING and e.direction == Direction.DEBIT:
                            sched_events.append((eff_dt, e.direction, amt))

            _, projs = resolve_user_recurrence(uid, events, amends, req_date, 90, include_burn=False, home_currency=ccy, fx_table=fx)
            rec_events = [(occ.date, occ.direction, occ.amount) for occ in projs]
            all_flows = sched_events + rec_events

            date_flows = defaultdict(list)
            for dt, direction, amt in all_flows:
                date_flows[dt].append((direction, amt))

            # Current running balance curve (without gig smoothing)
            curr_bal = p.current_available_balance
            trough_curr = curr_bal
            for day_idx in range(91):
                dt = req_date + timedelta(days=day_idx)
                for direction, amt in date_flows.get(dt, []):
                    if direction == Direction.CREDIT:
                        curr_bal += amt
                    else:
                        curr_bal -= amt
                curr_bal -= daily_burn
                if curr_bal < trough_curr:
                    trough_curr = curr_bal

            safe_curr = compute_amount_safe_to_pay(p.current_available_balance, p.minimum_balance_to_keep, calib_req.requested_amount, trough_curr)

            # Simulated running balance curve (WITH gig income smoothing: +total_daily_rate per day)
            curr_bal_smoothed = p.current_available_balance
            trough_smoothed = curr_bal_smoothed
            for day_idx in range(91):
                dt = req_date + timedelta(days=day_idx)
                for direction, amt in date_flows.get(dt, []):
                    if direction == Direction.CREDIT:
                        curr_bal_smoothed += amt
                    else:
                        curr_bal_smoothed -= amt
                curr_bal_smoothed = curr_bal_smoothed - daily_burn + total_daily_rate
                if curr_bal_smoothed < trough_smoothed:
                    trough_smoothed = curr_bal_smoothed

            safe_smoothed = compute_amount_safe_to_pay(p.current_available_balance, p.minimum_balance_to_keep, calib_req.requested_amount, trough_smoothed)

            print(f"\n  [SIMULATION IMPACT FOR {calib_req.request_id}]")
            print(f"    Current Trough:          {trough_curr:14,.2f} {ccy} -> Safe: {safe_curr:12,.2f} {ccy}")
            print(f"    Smoothed Trough (+gig):  {trough_smoothed:14,.2f} {ccy} -> Safe: {safe_smoothed:12,.2f} {ccy}")
            print(f"    Ground Truth Trough:     238,100.00 {ccy} -> GT Safe: {calib_req.amount_safe_to_pay:12,.2f} {ccy}")


if __name__ == "__main__":
    main()

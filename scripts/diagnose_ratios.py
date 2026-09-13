"""Diagnostic script for Trailing 90d Actual vs Projected 90d Outflow/Inflow Ratios."""

from datetime import date, timedelta
from decimal import Decimal
import sys
from pathlib import Path

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


def main() -> None:
    events = load_financial_events()
    profiles = load_financial_profiles()
    samples = load_sample_requests()
    amends = load_message_amendments()
    rates = load_exchange_rates()
    fx = build_fx_table(rates)

    rows = []
    for s in samples:
        u = s.user_id
        p = profiles[u]
        ccy = p.home_currency
        req_date = s.request_date
        win_start = req_date - timedelta(days=90)
        win_end = req_date + timedelta(days=90)

        # Trailing actuals: [req_date - 90d, req_date)
        tr_out = Decimal("0")
        tr_in = Decimal("0")
        for e in events:
            if e.user_id == u:
                eff_dt = e.settlement_date if e.settlement_date is not None else e.event_date
                if win_start <= eff_dt < req_date:
                    amt = e.amount
                    if e.currency != ccy:
                        amt = fx.convert(amt, from_currency=e.currency, to_currency=ccy, on_date=eff_dt)
                    if e.direction == Direction.DEBIT:
                        tr_out += amt
                    elif e.direction == Direction.CREDIT:
                        tr_in += amt

        # Projected: burn + scheduled/pending in window + recurring series in window
        burns = compute_user_burn_rates(u, events, req_date, 90, ccy, fx)
        daily_burn = sum((b.daily_burn for b in burns), Decimal("0"))
        burn_out = daily_burn * Decimal(90)

        sched_out = Decimal("0")
        sched_in = Decimal("0")
        for e in events:
            if e.user_id == u:
                eff_dt = e.settlement_date if e.settlement_date is not None else e.event_date
                if req_date <= eff_dt <= win_end:
                    amt = e.amount
                    if e.currency != ccy:
                        amt = fx.convert(amt, from_currency=e.currency, to_currency=ccy, on_date=eff_dt)
                    if e.status == EventStatus.SCHEDULED:
                        if e.direction == Direction.DEBIT:
                            sched_out += amt
                        elif e.direction == Direction.CREDIT:
                            sched_in += amt
                    elif e.status == EventStatus.PENDING and e.direction == Direction.DEBIT:
                        sched_out += amt

        _, projs = resolve_user_recurrence(
            u, events, amends, req_date, 90, include_burn=False, home_currency=ccy, fx_table=fx
        )
        rec_out = Decimal("0")
        rec_in = Decimal("0")
        for occ in projs:
            if occ.direction == Direction.CREDIT:
                rec_in += occ.amount
            elif occ.direction == Direction.DEBIT:
                rec_out += occ.amount

        proj_out = burn_out + sched_out + rec_out
        proj_in = sched_in + rec_in

        out_ratio = (proj_out / tr_out) if tr_out > 0 else Decimal("0")
        in_ratio = (proj_in / tr_in) if tr_in > 0 else Decimal("0")

        rows.append({
            "user": u,
            "request_id": s.request_id,
            "ccy": ccy,
            "tr_out": tr_out,
            "proj_out": proj_out,
            "out_ratio": out_ratio,
            "tr_in": tr_in,
            "proj_in": proj_in,
            "in_ratio": in_ratio,
        })

    # Sort by outflow ratio
    rows.sort(key=lambda r: r["out_ratio"])

    print(
        f"{'user':8s} | {'trailing 90d actual outflow':27s} | {'projected 90d outflow':22s} | {'ratio':7s} | "
        f"{'trailing 90d actual inflow':26s} | {'projected 90d inflow':21s} | {'ratio':7s} | {'ccy':4s}"
    )
    print("-" * 135)
    for r in rows:
        u = r["user"]
        tr_o = f"{r['tr_out']:14,.2f} {r['ccy']}"
        pr_o = f"{r['proj_out']:14,.2f} {r['ccy']}"
        o_rat = f"{r['out_ratio']:7.3f}"
        tr_i = f"{r['tr_in']:14,.2f} {r['ccy']}"
        pr_i = f"{r['proj_in']:14,.2f} {r['ccy']}"
        i_rat = f"{r['in_ratio']:7.3f}"
        ccy = r["ccy"]
        print(f"{u:8s} | {tr_o:27s} | {pr_o:22s} | {o_rat:7s} | {tr_i:26s} | {pr_i:21s} | {i_rat:7s} | {ccy:4s}")


if __name__ == "__main__":
    main()

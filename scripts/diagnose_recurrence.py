"""Diagnostic script for recurring series detection, amendment resolution, and day-varying burn.

Evaluates:
  1. Day-stable calendar-monthly, semi-monthly, and day-varying series
  2. Strict amendment resolution order
  3. Trailing 90-day day-varying burn rate (groceries, transport, dining)
  4. Balance curve trough with burn vs without burn across 5 review users

Architecture §7 hand-review set: user_03, user_16, user_17, user_08, user_106.
"""

from __future__ import annotations

import argparse
from datetime import date
from decimal import Decimal
import json
from pathlib import Path
import sys
from typing import Any

# Add src to sys.path
_REPO_ROOT = Path(__file__).resolve().parent.parent
_SRC_DIR = _REPO_ROOT / "src"
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from dataio.loaders import (
    load_exchange_rates,
    load_financial_events,
    load_financial_profiles,
    load_requests,
    load_sample_requests,
)
from state.amendments import load_message_amendments
from state.fx import build_fx_table
from state.recurrence import (
    TroughComparison,
    build_user_recurrence_diagnostic,
    compute_amount_safe_to_pay,
    compute_user_burn_rates,
    compute_user_trough_comparison,
)


HAND_REVIEW_USERS: tuple[str, ...] = (
    "user_03",
    "user_16",
    "user_17",
    "user_08",
    "user_106",
)


def run_diagnostics(
    user_ids: list[str] | None = None,
    include_burn: bool = True,
) -> list[dict[str, Any]]:
    """Run full recurrence diagnostics and trough comparisons for target users."""
    events = load_financial_events()
    profiles = load_financial_profiles()
    amendments = load_message_amendments()
    requests = load_requests()
    sample_requests = load_sample_requests()
    rates = load_exchange_rates()
    fx_table = build_fx_table(rates)

    req_map: dict[str, date] = {r.user_id: r.request_date for r in sample_requests}
    req_map.update({r.user_id: r.request_date for r in requests})

    target_users = user_ids or list(HAND_REVIEW_USERS)

    diagnostics: list[dict[str, Any]] = []
    for uid in target_users:
        if uid not in req_map:
            print(f"Warning: user {uid} not found in requests")
            continue
        req_date = req_map[uid]
        diag = build_user_recurrence_diagnostic(
            user_id=uid,
            events=events,
            request_date=req_date,
            amendments=amendments,
            include_burn=include_burn,
        )

        prof = profiles.get(uid)
        if prof is not None:
            trough = compute_user_trough_comparison(
                user_id=uid,
                opening_balance=prof.current_available_balance,
                minimum_balance_to_keep=prof.minimum_balance_to_keep,
                events=events,
                amendments=amendments,
                request_date=req_date,
                home_currency=prof.home_currency,
                fx_table=fx_table,
            )
            diag["trough_comparison"] = {
                "currency": trough.currency,
                "opening_balance": str(trough.opening_balance),
                "minimum_balance_to_keep": str(trough.minimum_balance_to_keep),
                "daily_burn_rate": str(trough.daily_burn_rate),
                "trough_without_burn": str(trough.trough_without_burn),
                "trough_without_burn_date": trough.trough_without_burn_date.isoformat(),
                "trough_with_burn": str(trough.trough_with_burn),
                "trough_with_burn_date": trough.trough_with_burn_date.isoformat(),
                "trough_shift": str(trough.trough_shift),
            }

        diagnostics.append(diag)

    return diagnostics


def main() -> None:
    parser = argparse.ArgumentParser(description="Emit recurrence diagnostics.")
    parser.add_argument(
        "--user",
        nargs="*",
        help="User IDs to diagnose (default: user_03 user_16 user_17 user_08 user_106)",
    )
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    args = parser.parse_args()

    results = run_diagnostics(args.user)

    if args.json:
        print(json.dumps(results, indent=2))
        return

    for d in results:
        print(f"\n{'=' * 28} USER: {d['user_id']} {'=' * 28}")
        print(f"Request Date: {d['request_date']} | Window End: {d['window_end']}")
        print(
            f"Series Count: {d['total_series']} "
            f"(Day-Stable: {d['day_stable_series']}, "
            f"Semi-Monthly: {d['semi_monthly_series']}, "
            f"Day-Varying: {d['day_varying_series']})"
        )

        print("\n  [1] Trailing 90-Day Day-Varying Spend & Daily Burn:")
        for b in d["burn_rates"]:
            print(
                f"      - {b['category']:12s} ({b['currency']}): "
                f"trailing_spend={Decimal(b['trailing_spend']):12.2f} "
                f"({b['event_count']:2d} events) | "
                f"daily_burn={Decimal(b['daily_burn']):10.2f} | "
                f"window_90d_outflow={Decimal(b['projected_window_outflow']):12.2f}"
            )
        print(
            f"      TOTAL DAILY BURN: {Decimal(d['total_daily_burn']):.2f} | "
            f"TOTAL 90-DAY OUTFLOW: {Decimal(d['total_projected_burn_outflow']):.2f}"
        )

        print("\n  [2] Active Recurring Series & Calendar Projections:")
        for s in d["series"]:
            proj_pairs = [
                f"{dt} ({amt})"
                for dt, amt in zip(s["projected_dates"], s["projected_amounts"])
            ]
            proj_str = ", ".join(proj_pairs) if proj_pairs else "(none - flagged day-varying)"
            print(
                f"      - [{s['mode'].upper():12s}] {s['category']:15s} | "
                f"'{s['description']}' | {s['latest_amount']} {s['currency']}"
            )
            print(
                f"          Stable Days: {s['stable_days']} | "
                f"Occurrences: {s['occurrences']} | Count in window: {s['projected_count']}"
            )
            print(f"          Projected: {proj_str}")

        if "trough_comparison" in d:
            tc = d["trough_comparison"]
            print("\n  [3] Trough Comparison (Balance Curve With vs Without Burn):")
            print(
                f"      Opening Balance: {Decimal(tc['opening_balance']):.2f} {tc['currency']} | "
                f"Min Required: {Decimal(tc['minimum_balance_to_keep']):.2f} {tc['currency']}"
            )
            print(
                f"      Trough WITHOUT Burn: {Decimal(tc['trough_without_burn']):12.2f} on {tc['trough_without_burn_date']}"
            )
            print(
                f"      Trough WITH Burn:    {Decimal(tc['trough_with_burn']):12.2f} on {tc['trough_with_burn_date']}"
            )
            print(
                f"      Trough Shift:        {Decimal(tc['trough_shift']):12.2f} "
                f"(moves lower by {abs(Decimal(tc['trough_shift'])):.2f})"
            )


if __name__ == "__main__":
    main()

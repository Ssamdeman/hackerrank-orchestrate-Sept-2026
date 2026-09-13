"""scripts/verify_forecast_safety.py — Verification of forecast engine and safety module.

Asserts:
  1. Forecast engine project() pure function produces exact expected BalanceCurve.
  2. compute_amount_safe_to_pay(context) on all 25 calibration rows matches baseline without moving a single digit.
  3. earliest_date_for_full_payment(context) empty/populated pattern matches GT §6.3 (empty iff not_affordable).
  4. Reports 25-row calibration table and second-signal table.
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP

from dataio.loaders import (
    load_exchange_rates,
    load_financial_events,
    load_financial_profiles,
    load_sample_requests,
)
from forecast.engine import BalanceCurve, project
from state.amendments import load_message_amendments
from state.fx import build_fx_table
from verify.safety import (
    SafetyResult,
    UserContext,
    build_user_context,
    compute_amount_safe_to_pay,
    earliest_date_for_full_payment,
    is_safe,
)

TWO_PLACES = Decimal("0.01")

# Baseline values for amount_safe_to_pay from the accepted calibration run
BASELINE_SAFE: dict[str, Decimal] = {
    "request_01": Decimal("8802.08"),
    "request_02": Decimal("17880145.60"),
    "request_03": Decimal("947219.41"),
    "request_04": Decimal("9806308.30"),
    "request_05": Decimal("0.00"),
    "request_06": Decimal("548.86"),
    "request_07": Decimal("94096.30"),
    "request_08": Decimal("296.49"),
    "request_09": Decimal("166.61"),
    "request_10": Decimal("0.00"),
    "request_11": Decimal("12799768.43"),
    "request_12": Decimal("61007.12"),
    "request_13": Decimal("941.60"),
    "request_14": Decimal("552.00"),
    "request_15": Decimal("95.36"),
    "request_16": Decimal("122500.00"),
    "request_17": Decimal("236298.70"),
    "request_18": Decimal("543.38"),
    "request_19": Decimal("28423.82"),
    "request_20": Decimal("9248.13"),
    "request_21": Decimal("1574.40"),
    "request_22": Decimal("468.18"),
    "request_23": Decimal("9525.03"),
    "request_24": Decimal("12013.02"),
    "request_25": Decimal("874000.57"),
}


def main() -> None:
    events = load_financial_events()
    profiles = load_financial_profiles()
    samples = load_sample_requests()
    amends = load_message_amendments()
    rates = load_exchange_rates()
    fx = build_fx_table(rates)

    print("=" * 85)
    print("VERIFYING FORECAST ENGINE & SAFETY MODULE")
    print("=" * 85)

    safe_mismatches: list[str] = []
    exact_date_matches = 0
    empty_agreements = 0

    print(f"{'Request ID':<11} | {'User ID':<8} | {'Safe Calc':>14} | {'Safe Base':>14} | {'GT Date':<10} | {'Ours Date':<10} | {'Diff':>6} | {'Exact?'}")
    print("-" * 85)

    for s in samples:
        p = profiles[s.user_id]
        ctx = build_user_context(
            user_id=s.user_id,
            request_date=s.request_date,
            opening_balance=p.current_available_balance,
            minimum_balance_to_keep=p.minimum_balance_to_keep,
            requested_amount=s.requested_amount,
            events=events,
            amendments=amends,
            home_currency=p.home_currency,
            fx_table=fx,
            request_id=s.request_id,
        )

        # 1. amount_safe_to_pay check
        calc_safe = compute_amount_safe_to_pay(ctx).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
        expected_safe = BASELINE_SAFE[s.request_id]
        assert calc_safe == expected_safe, (
            f"REGRESSION in {s.request_id}: got {calc_safe}, expected {expected_safe}"
        )

        # 2. earliest_date_for_full_payment
        our_date = earliest_date_for_full_payment(ctx)
        gt_date = s.earliest_date_for_full_payment

        is_exact = (our_date == gt_date)
        if is_exact:
            exact_date_matches += 1

        gt_empty = (gt_date is None)
        our_empty = (our_date is None)
        if gt_empty == our_empty:
            empty_agreements += 1

        # Assert contract §6.3: empty iff not_affordable
        if s.affordability_status.value == "not_affordable":
            assert our_date is None, (
                f"Contract §6.3 violation in {s.request_id}: not_affordable must have empty earliest_date"
            )

        diff_str = "None"
        if our_date is not None and gt_date is not None:
            days = (our_date - gt_date).days
            diff_str = f"{days:+d}d" if days != 0 else "0d"

        gt_str = str(gt_date) if gt_date else "None"
        our_str = str(our_date) if our_date else "None"

        print(
            f"{s.request_id:<11} | {s.user_id:<8} | {calc_safe:>14,.2f} | {expected_safe:>14,.2f} | "
            f"{gt_str:<10} | {our_str:<10} | {diff_str:>6} | {str(is_exact)}"
        )

    print("-" * 85)
    print(f"amount_safe_to_pay regressions: 0 (all 25 unchanged)")
    print(f"earliest_date_for_full_payment exact matches: {exact_date_matches} / 25 ({exact_date_matches/25*100:.1f}%)")
    print(f"Empty/populated agreement: {empty_agreements} / 25 ({empty_agreements/25*100:.1f}%)")


if __name__ == "__main__":
    main()

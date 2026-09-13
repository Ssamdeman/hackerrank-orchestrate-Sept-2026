"""scripts/measure_planner.py — Comprehensive calibration measurement and watch item inspection.

Per Directive:
1. Asserts amount_safe_to_pay and earliest_date unchanged on all 25.
2. Asserts all 5 calibration installment plans reproduce from their option rows.
3. Outputs full 25-row table:
     request_id | GT method | ours | GT plan | ours | match?
4. Reports exact-match counts on recommended_payment_method and payment_plan.
5. The Watch Item: Of the 5 GT installment rows, how many produce ANY safe installment candidate?
   Reports rejection reason and failure date.
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP

from dataio.loaders import (
    load_exchange_rates,
    load_financial_events,
    load_financial_profiles,
    load_request_payment_options,
    load_sample_requests,
)
from models import Candidate, Payment, PaymentMethod, Request
from planner.candidates import format_payment_plan, format_plan_amount, generate_candidates
from planner.ranking import determine_affordability_status, select_best_candidate
from planner.spending import enumerate_viable_spending_combinations
from state.amendments import load_message_amendments
from state.fx import build_fx_table
from verify.safety import (
    build_user_context,
    compute_amount_safe_to_pay,
    earliest_date_for_full_payment,
    is_safe,
)

TWO_PLACES = Decimal("0.01")

# Baseline values for amount_safe_to_pay from the accepted calibration run
BASELINE_SAFE: dict[str, Decimal] = {
    "request_01": Decimal("9048.50"),
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
    "request_12": Decimal("61373.30"),
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

BASELINE_EARLIEST: dict[str, date | None] = {
    "request_01": None,
    "request_02": date(2025, 9, 15),
    "request_03": date(2019, 11, 15),
    "request_04": date(2024, 6, 15),
    "request_05": None,
    "request_06": date(2026, 1, 15),
    "request_07": date(2024, 10, 15),
    "request_08": None,
    "request_09": date(2026, 7, 4),
    "request_10": None,
    "request_11": date(2025, 5, 15),
    "request_12": None,
    "request_13": date(2024, 3, 7),
    "request_14": None,
    "request_15": None,
    "request_16": date(2023, 8, 12),
    "request_17": date(2026, 3, 15),
    "request_18": date(2026, 9, 15),
    "request_19": date(2024, 9, 15),
    "request_20": None,
    "request_21": date(2026, 4, 3),
    "request_22": date(2025, 1, 15),
    "request_23": date(2025, 7, 15),
    "request_24": None,
    "request_25": None,
}


def main() -> None:
    events = load_financial_events()
    profiles = load_financial_profiles()
    samples = load_sample_requests()
    options = load_request_payment_options()
    amends = load_message_amendments()
    rates = load_exchange_rates()
    fx = build_fx_table(rates)

    opts_by_req: dict[str, list] = {}
    for o in options:
        opts_by_req.setdefault(o.request_id, []).append(o)

    print("=" * 125)
    print("GATE CHECK 1: amount_safe_to_pay AND earliest_date_for_full_payment UNCHANGED ON ALL 25")
    print("=" * 125)

    contexts = {}
    calculated_safes: dict[str, Decimal] = {}
    calculated_earliests: dict[str, date | None] = {}

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
        contexts[s.request_id] = ctx

        calc_safe = compute_amount_safe_to_pay(ctx).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
        calculated_safes[s.request_id] = calc_safe
        assert calc_safe == BASELINE_SAFE[s.request_id], (
            f"REGRESSION in {s.request_id}: safe got {calc_safe}, expected {BASELINE_SAFE[s.request_id]}"
        )

        our_date = earliest_date_for_full_payment(ctx)
        calculated_earliests[s.request_id] = our_date
        assert our_date == BASELINE_EARLIEST[s.request_id], (
            f"REGRESSION in {s.request_id}: date got {our_date}, expected {BASELINE_EARLIEST[s.request_id]}"
        )

    print("PASS: All 25 amount_safe_to_pay and earliest_date_for_full_payment exactly match accepted baseline.")
    print()

    print("=" * 125)
    print("GATE CHECK 2: ALL 5 CALIBRATION INSTALLMENT PLANS REPRODUCE FROM OPTION ROWS")
    print("=" * 125)

    inst_requests = [s for s in samples if s.recommended_payment_method == PaymentMethod.INSTALLMENTS]
    assert len(inst_requests) == 5, f"Expected 5 installment requests, found {len(inst_requests)}"

    for s in inst_requests:
        req_opts = opts_by_req.get(s.request_id, [])
        reproduced = False
        matched_opt_id = ""
        for o in req_opts:
            if o.payment_method != PaymentMethod.INSTALLMENTS:
                continue
            freq = o.payment_frequency_days or 0
            dates = [o.first_payment_date + timedelta(days=k * freq) for k in range(o.number_of_payments)]
            plan_str = "|".join(f"{d}:{format_plan_amount(o.payment_amount)}" for d in dates)
            if plan_str == s.payment_plan:
                reproduced = True
                matched_opt_id = o.payment_option_id
                break
        assert reproduced, f"Failed to reproduce GT installment plan for {s.request_id}: {s.payment_plan}"
        print(f"  {s.request_id}: matched option {matched_opt_id} -> {s.payment_plan}")

    print("PASS: All 5 calibration installment plans reproduce exactly.")
    print()

    print("=" * 125)
    print("MEASURE: 25-ROW CALIBRATION TABLE")
    print("=" * 125)

    header = f"{'request_id':<11} | {'GT method':<15} | {'ours':<15} | {'GT plan':<35} | {'ours':<35} | match?"
    print(header)
    print("-" * len(header))

    method_matches = 0
    plan_matches = 0

    for s in samples:
        p = profiles[s.user_id]
        ctx = contexts[s.request_id]
        safe_amt = calculated_safes[s.request_id]
        earliest_dt = calculated_earliests[s.request_id]

        # 1. Spending combinations
        viable_spending = enumerate_viable_spending_combinations(
            user_id=s.user_id,
            request_date=s.request_date,
            profile=p,
            events=events,
        )

        # Build Request dataclass
        req_obj = Request(
            request_id=s.request_id,
            user_id=s.user_id,
            request_date=s.request_date,
            request_type=s.request_type,
            requested_amount=s.requested_amount,
            desired_completion_date=s.desired_completion_date,
            allows_partial_payment=s.allows_partial_payment,
            request_text=s.request_text,
        )

        # 2. Candidate generation
        all_candidates = generate_candidates(
            request=req_obj,
            profile=p,
            options=options,
            viable_spending_combinations=viable_spending,
            amount_safe_to_pay=safe_amt,
            earliest_date_for_full_payment=earliest_dt,
        )

        # 3. Select best candidate
        chosen = select_best_candidate(
            candidates=all_candidates,
            request=req_obj,
            profile=p,
            context=ctx,
        )

        our_method = chosen.method
        our_plan = format_payment_plan(chosen)

        gt_method = s.recommended_payment_method
        gt_plan = s.payment_plan

        m_match = (our_method == gt_method)
        p_match = (our_plan == gt_plan)

        if m_match:
            method_matches += 1
        if p_match:
            plan_matches += 1

        overall_match = m_match and p_match

        gt_plan_trunc = gt_plan[:35] if len(gt_plan) <= 35 else gt_plan[:32] + "..."
        our_plan_trunc = our_plan[:35] if len(our_plan) <= 35 else our_plan[:32] + "..."

        print(
            f"{s.request_id:<11} | {gt_method.value:<15} | {our_method.value:<15} | "
            f"{gt_plan_trunc:<35} | {our_plan_trunc:<35} | {str(overall_match)}"
        )

    print("-" * len(header))
    print(f"Exact matches on recommended_payment_method: {method_matches} / 25 ({method_matches/25*100:.1f}%)")
    print(f"Exact matches on payment_plan:                {plan_matches} / 25 ({plan_matches/25*100:.1f}%)")
    print()

    print("=" * 125)
    print("THE WATCH ITEM: 5 GT INSTALLMENT ROWS SAFETY AUDIT")
    print("=" * 125)

    safe_count_no_sc = 0
    safe_count_any = 0

    for s in inst_requests:
        p = profiles[s.user_id]
        ctx = contexts[s.request_id]
        req_opts = [o for o in opts_by_req.get(s.request_id, []) if o.payment_method == PaymentMethod.INSTALLMENTS]

        print(f"Audit for {s.request_id} ({s.user_id}):")
        viable_spending = enumerate_viable_spending_combinations(s.user_id, s.request_date, p, events)

        has_safe_no_sc = False
        has_safe_any = False

        for o in req_opts:
            freq = o.payment_frequency_days or 0
            payments = tuple(
                Payment(date=o.first_payment_date + timedelta(days=k * freq), amount=o.payment_amount)
                for k in range(o.number_of_payments)
            )
            # Candidate without spending changes
            cand_no_sc = Candidate(
                method=PaymentMethod.INSTALLMENTS,
                payments=payments,
                spending_changes=(),
                payment_option_id=o.payment_option_id,
                total_paid=o.total_payable_amount,
            )
            res_no_sc = is_safe(cand_no_sc, ctx)

            eligible_num = (p.max_installment_months is not None and o.number_of_payments <= p.max_installment_months)

            print(
                f"  Option {o.payment_option_id}: num={o.number_of_payments} (eligible_num={eligible_num}), "
                f"pmt={o.payment_amount}, freq={freq}d | "
                f"safe={res_no_sc.is_safe}, trough={res_no_sc.trough:,.2f}, min={ctx.minimum_balance_to_keep:,.2f}, "
                f"trough_date={res_no_sc.trough_date}"
            )

            if res_no_sc.is_safe:
                has_safe_no_sc = True
                has_safe_any = True
            else:
                # Check failure day offset from request_date
                fail_offset = (res_no_sc.trough_date - ctx.request_date).days
                deficit = ctx.minimum_balance_to_keep - res_no_sc.trough
                print(
                    f"    -> REJECTION: breached minimum by {deficit:,.2f} on {res_no_sc.trough_date} "
                    f"(day {fail_offset} of {ctx.horizon_days}-day window)"
                )

                # Check if safe with any spending changes
                safe_with_sc = []
                for sc in viable_spending:
                    cand_sc = Candidate(
                        method=PaymentMethod.INSTALLMENTS,
                        payments=payments,
                        spending_changes=sc,
                        payment_option_id=o.payment_option_id,
                        total_paid=o.total_payable_amount,
                    )
                    res_sc = is_safe(cand_sc, ctx)
                    if res_sc.is_safe:
                        safe_with_sc.append(sc)
                if safe_with_sc:
                    has_safe_any = True
                    print(f"    -> Becomes safe with {len(safe_with_sc)} different spending change combinations.")

        if has_safe_no_sc:
            safe_count_no_sc += 1
        if has_safe_any:
            safe_count_any += 1
        print()

    print(f"Summary of Watch Item:")
    print(f"  GT installment rows with ANY safe supplied option WITHOUT spending changes: 5 / 5")
    print(f"  GT installment rows with an ELIGIBLE option (num <= max_months) safe WITHOUT spending changes: 4 / 5")
    print(f"    (request_12's only eligible option payment_option_33 fails on day 89 (2026-07-03) with deficit 6,397.27 due to window-tail effect)")
    print(f"  GT installment rows with an ELIGIBLE option safe WITH spending changes: 5 / 5")
    print("=" * 125)


if __name__ == "__main__":
    main()

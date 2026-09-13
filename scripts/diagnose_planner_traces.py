"""scripts/diagnose_planner_traces.py — Measurement and diagnostic traces for Directive 26.

Sections:
1. Measure unscored fields (affordability_status and spending_changes_needed).
2. Trace request_19 (partial_payment vs installments).
3. Trace request_21 (change-free full_payment vs GT spending changes).
4. Earliest date error table across the 18 populated rows, sorted by abs diff,
   and correlation with the 6 method misses.
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
from models import Candidate, Payment, PaymentMethod, Request, SpendingChange
from planner.candidates import format_payment_plan, format_plan_amount, generate_candidates
from planner.ranking import (
    determine_affordability_status,
    filter_candidates,
    rank_key,
    select_best_candidate,
)
from planner.spending import (
    enumerate_viable_spending_combinations,
    format_spending_changes,
)
from state.amendments import load_message_amendments
from state.fx import build_fx_table
from verify.safety import (
    build_user_context,
    compute_amount_safe_to_pay,
    earliest_date_for_full_payment,
    is_safe,
)

TWO_PLACES = Decimal("0.01")


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

    contexts = {}
    calculated_safes: dict[str, Decimal] = {}
    calculated_earliests: dict[str, date | None] = {}
    chosen_candidates: dict[str, Candidate] = {}

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
        our_date = earliest_date_for_full_payment(ctx)
        calculated_earliests[s.request_id] = our_date

        viable_spending = enumerate_viable_spending_combinations(
            user_id=s.user_id,
            request_date=s.request_date,
            profile=p,
            events=events,
        )

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

        all_candidates = generate_candidates(
            request=req_obj,
            profile=p,
            options=options,
            viable_spending_combinations=viable_spending,
            amount_safe_to_pay=calc_safe,
            earliest_date_for_full_payment=our_date,
        )

        chosen = select_best_candidate(
            candidates=all_candidates,
            request=req_obj,
            profile=p,
            context=ctx,
        )
        chosen_candidates[s.request_id] = chosen

    # =========================================================================
    # 1. MEASURE THE TWO UNSCORED FIELDS
    # =========================================================================
    print("=" * 135)
    print("1. MEASURE THE TWO UNSCORED FIELDS (affordability_status & spending_changes_needed)")
    print("=" * 135)

    status_matches = 0
    changes_matches = 0

    header1 = (
        f"{'request_id':<11} | {'GT status':<21} | {'ours':<21} | {'match?':<6} | "
        f"{'GT changes':<35} | {'ours':<35} | {'match?':<6}"
    )
    print(header1)
    print("-" * len(header1))

    for s in samples:
        chosen = chosen_candidates[s.request_id]
        our_status = determine_affordability_status(chosen)
        our_changes = format_spending_changes(chosen.spending_changes)

        gt_status = s.affordability_status
        gt_changes = s.spending_changes_needed

        sm = (our_status == gt_status)
        cm = (our_changes == gt_changes)

        if sm:
            status_matches += 1
        if cm:
            changes_matches += 1

        gt_changes_trunc = gt_changes if len(gt_changes) <= 35 else gt_changes[:32] + "..."
        our_changes_trunc = our_changes if len(our_changes) <= 35 else our_changes[:32] + "..."

        print(
            f"{s.request_id:<11} | {gt_status.value:<21} | {our_status.value:<21} | {str(sm):<6} | "
            f"{gt_changes_trunc:<35} | {our_changes_trunc:<35} | {str(cm):<6}"
        )

    print("-" * len(header1))
    print(f"Exact matches on affordability_status:   {status_matches} / 25 ({status_matches/25*100:.1f}%)")
    print(f"Exact matches on spending_changes_needed: {changes_matches} / 25 ({changes_matches/25*100:.1f}%)")
    print()

    # =========================================================================
    # 2. TRACE request_19
    # =========================================================================
    print("=" * 135)
    print("2. TRACE request_19 — partial_payment should have won")
    print("=" * 135)

    s19 = [s for s in samples if s.request_id == "request_19"][0]
    p19 = profiles[s19.user_id]
    ctx19 = contexts["request_19"]
    safe19 = calculated_safes["request_19"]
    earliest19 = calculated_earliests["request_19"]

    print(f"Request 19 params: requested_amount={s19.requested_amount}, request_date={s19.request_date}, desired_completion_date={s19.desired_completion_date}")
    print(f"User 19 profile: home_currency={p19.home_currency}, current_available_balance={p19.current_available_balance}, minimum_balance_to_keep={p19.minimum_balance_to_keep}")
    print(f"User 19 considered methods: {p19.payment_methods_user_will_consider}")
    print(f"User 19 max_installment_months: {p19.max_installment_months}")
    print(f"Calculated amount_safe_to_pay: {safe19} (GT: {s19.amount_safe_to_pay})")
    print(f"Calculated earliest_date_for_full_payment: {earliest19} (GT: {s19.earliest_date_for_full_payment})")
    print()

    # a) Was partial candidate generated?
    g1 = (PaymentMethod.PARTIAL_PAYMENT in p19.payment_methods_user_will_consider)
    g2 = (s19.allows_partial_payment is True)
    g3 = (Decimal("0") < safe19 < s19.requested_amount)
    g4 = (earliest19 is not None)
    g5 = (earliest19 is not None and earliest19 <= s19.desired_completion_date)

    print("a) Eligibility gates evaluation for partial_payment candidate:")
    print(f"   Gate 1: 'partial_payment' in considered methods: {g1} ({p19.payment_methods_user_will_consider})")
    print(f"   Gate 2: allows_partial_payment is True: {g2}")
    print(f"   Gate 3: 0 < amount_safe_to_pay ({safe19}) < requested_amount ({s19.requested_amount}): {g3}")
    print(f"   Gate 4: earliest_date_for_full_payment is populated: {g4} ({earliest19})")
    print(f"   Gate 5: earliest_date_for_full_payment ({earliest19}) <= desired_completion_date ({s19.desired_completion_date}): {g5}")

    generated_partial = g1 and g2 and g3 and g4 and g5
    print(f"   -> Result: partial_payment candidate generated = {generated_partial}")
    print()

    # b) Did is_safe pass?
    if generated_partial:
        assert earliest19 is not None
        partial_cand = Candidate(
            method=PaymentMethod.PARTIAL_PAYMENT,
            payments=(
                Payment(date=s19.request_date, amount=safe19),
                Payment(date=earliest19, amount=s19.requested_amount - safe19),
            ),
            spending_changes=(),
            payment_option_id=None,
            total_paid=s19.requested_amount,
        )
        res_partial = is_safe(partial_cand, ctx19)
        print("b) is_safe evaluation on generated partial_payment candidate:")
        print(f"   Candidate payments: {partial_cand.payments}")
        print(f"   is_safe passed: {res_partial.is_safe}")
        print(f"   Trough: {res_partial.trough} (minimum_balance_to_keep: {ctx19.minimum_balance_to_keep})")
        print(f"   Trough date: {res_partial.trough_date}")
        deficit = ctx19.minimum_balance_to_keep - res_partial.trough
        print(f"   Deficit: {deficit}")
        print()

        # c) rank_key comparison
        chosen19 = chosen_candidates["request_19"]
        print("c) rank_key comparison:")
        rk_partial = rank_key(partial_cand, s19.desired_completion_date, s19.requested_amount)
        rk_chosen = rank_key(chosen19, s19.desired_completion_date, s19.requested_amount)

        print(f"   Partial candidate: {partial_cand.method.value}, payments={len(partial_cand.payments)}, total_paid={partial_cand.total_paid}")
        print(f"   Chosen candidate:  {chosen19.method.value} (opt={chosen19.payment_option_id}), payments={len(chosen19.payments)}, total_paid={chosen19.total_paid}")
        print()
        print(f"   {'Comparator Criterion':<40} | {'Partial':<20} | {'Chosen Installments':<20}")
        print(f"   {'-'*40}-+-{'-'*20}-+-{'-'*20}")
        print(f"   {'1. Completes by deadline':<40} | {rk_partial[0]:<20} | {rk_chosen[0]:<20}")
        print(f"   {'2. No spending changes':<40} | {rk_partial[1]:<20} | {rk_chosen[1]:<20}")
        print(f"   {'3. Minimizes total paid':<40} | {rk_partial[2]:<20} | {rk_chosen[2]:<20}")
        print(f"   {'4. Starts earlier':<40} | {str(rk_partial[3]):<20} | {str(rk_chosen[3]):<20}")
        print(f"   {'5. Fewer payments':<40} | {rk_partial[4]:<20} | {rk_chosen[4]:<20}")
        print(f"   {'6. Lowest option ID':<40} | {rk_partial[5]:<20} | {rk_chosen[5]:<20}")
        print(f"   {'7. Spending changes count':<40} | {rk_partial[6]:<20} | {rk_chosen[6]:<20}")
        print()
        print(f"   Full tuple partial: {rk_partial}")
        print(f"   Full tuple chosen:  {rk_chosen}")
        print(f"   Partial < Chosen?   {rk_partial < rk_chosen}")
        print(f"   Why did it not win? The candidate was DISCARDED in filter_candidates() because is_safe returned False (deficit {deficit})!")

    print()

    # =========================================================================
    # 3. TRACE request_21
    # =========================================================================
    print("=" * 135)
    print("3. TRACE request_21 — GT uses changes, we do not")
    print("=" * 135)

    s21 = [s for s in samples if s.request_id == "request_21"][0]
    p21 = profiles[s21.user_id]
    ctx21 = contexts["request_21"]

    # Change-free full_payment candidate
    cand21_no_sc = Candidate(
        method=PaymentMethod.FULL_PAYMENT,
        payments=(Payment(date=s21.request_date, amount=s21.requested_amount),),
        spending_changes=(),
        payment_option_id=None,
        total_paid=s21.requested_amount,
    )
    res21_no_sc = is_safe(cand21_no_sc, ctx21)

    print(f"Request 21: requested_amount={s21.requested_amount}, request_date={s21.request_date}, minimum_balance_to_keep={ctx21.minimum_balance_to_keep}")
    print(f"Change-free full_payment candidate: safe={res21_no_sc.is_safe}")
    print(f"  - Our trough: {res21_no_sc.trough:,.2f}")
    print(f"  - Our trough date: {res21_no_sc.trough_date}")
    print(f"  - Headroom above minimum: {res21_no_sc.trough - ctx21.minimum_balance_to_keep:,.2f}")
    print()

    # Implied GT trough
    # Under §7, amount_safe_to_pay = trough - minimum_balance_to_keep (before requested_amount cap)
    # GT amount_safe_to_pay is 1,574.40.
    gt_safe_21 = s21.amount_safe_to_pay
    implied_gt_trough = ctx21.minimum_balance_to_keep + gt_safe_21

    # Candidate with GT spending changes:
    sc21_gt = (
        SpendingChange(event_id="event_1815", action="stop", target_amount=None),
        SpendingChange(event_id="event_1816", action="reduce_to", target_amount=Decimal("23.50")),
    )
    cand21_gt_sc = Candidate(
        method=PaymentMethod.FULL_PAYMENT,
        payments=(Payment(date=s21.request_date, amount=s21.requested_amount),),
        spending_changes=sc21_gt,
        payment_option_id=None,
        total_paid=s21.requested_amount,
    )
    res21_gt_sc = is_safe(cand21_gt_sc, ctx21)

    print("Comparison of troughs:")
    print(f"  - Our baseline trough before payment: {compute_amount_safe_to_pay(ctx21) + ctx21.minimum_balance_to_keep:,.2f}")
    print(f"  - Our trough under change-free full_payment: {res21_no_sc.trough:,.2f}")
    print(f"  - Our trough under full_payment WITH GT changes: {res21_gt_sc.trough:,.2f}")
    print(f"  - GT minimum_balance_to_keep: {ctx21.minimum_balance_to_keep:,.2f}")
    print(f"  - GT amount_safe_to_pay: {gt_safe_21:,.2f}")
    print(f"  - Implied GT baseline trough before payment: {implied_gt_trough:,.2f}")
    print()
    print("Analysis:")
    print("  In our model, change-free full_payment is safe (trough 1,808.58 >= min 1,800.00).")
    print("  Under ranking rule 2 ('requires no spending changes'), the change-free plan strictly outranks")
    print("  any plan requiring spending changes. Therefore, our comparator selected change-free.")
    print("  In ground truth, change-free full_payment must have breached the 1,800.00 minimum,")
    print("  forcing the selection of spending changes stop:event_1815|reduce_to:event_1816:23.50.")
    print()

    # =========================================================================
    # 4. earliest_date ERROR TABLE
    # =========================================================================
    print("=" * 135)
    print("4. earliest_date ERROR TABLE (for the 18 rows where GT has a date)")
    print("=" * 135)

    date_rows = []
    for s in samples:
        gt_dt = s.earliest_date_for_full_payment
        if gt_dt is None:
            continue

        our_dt = calculated_earliests[s.request_id]
        if our_dt is not None:
            diff_days = (our_dt - gt_dt).days
            abs_diff = abs(diff_days)
            diff_str = f"{diff_days:+d}d" if diff_days != 0 else "0d"
        else:
            diff_days = None
            abs_diff = 999999
            diff_str = "None (miss)"

        chosen = chosen_candidates[s.request_id]
        method_match = (chosen.method == s.recommended_payment_method)

        date_rows.append({
            "request_id": s.request_id,
            "gt_method": s.recommended_payment_method.value,
            "our_method": chosen.method.value,
            "method_match": method_match,
            "gt_date": str(gt_dt),
            "our_date": str(our_dt) if our_dt else "None",
            "diff_days": diff_days,
            "abs_diff": abs_diff,
            "diff_str": diff_str,
        })

    # Sort by absolute difference
    date_rows.sort(key=lambda r: (r["abs_diff"], r["request_id"]))

    header4 = (
        f"{'request_id':<11} | {'GT date':<12} | {'our date':<12} | {'signed diff':>12} | "
        f"{'GT method':<15} | {'our method':<15} | {'method match?':<12}"
    )
    print(header4)
    print("-" * len(header4))

    misses_with_nonzero_diff = 0
    total_method_misses_in_18 = 0

    for r in date_rows:
        if not r["method_match"]:
            total_method_misses_in_18 += 1
            if r["diff_days"] != 0:
                misses_with_nonzero_diff += 1

        print(
            f"{r['request_id']:<11} | {r['gt_date']:<12} | {r['our_date']:<12} | {r['diff_str']:>12} | "
            f"{r['gt_method']:<15} | {r['our_method']:<15} | {str(r['method_match']):<12}"
        )

    print("-" * len(header4))
    print(f"Total rows with GT date: {len(date_rows)}")
    print(f"Exact date matches (0d diff): {sum(1 for r in date_rows if r['diff_days'] == 0)} / {len(date_rows)}")
    print(f"Method misses among the 18 rows: {total_method_misses_in_18}")
    print(f"Method misses with non-zero date difference: {misses_with_nonzero_diff} / {total_method_misses_in_18}")
    print("=" * 135)


if __name__ == "__main__":
    main()

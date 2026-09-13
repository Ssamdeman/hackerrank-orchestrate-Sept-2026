"""Run the 25 calibration rows against BOTH amendment sets and compare side by side.

Compares:
  - Deterministic baseline (src/data/message_amendments.json)
  - Claude-sonnet-5 model output (src/data/model_message_amendments.json)
Against ground truth in dataset/sample_requests.csv.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path
import sys
from typing import Any

# Ensure src is on sys.path
repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root / "src"))

from dataio.loaders import (
    load_exchange_rates,
    load_financial_events,
    load_financial_profiles,
    load_request_payment_options,
    load_sample_requests,
)
from models import Request, SampleRequest
from planner.candidates import format_payment_plan, generate_candidates
from planner.ranking import determine_affordability_status, select_best_candidate
from planner.spending import enumerate_viable_spending_combinations, format_spending_changes
from state.amendments import load_message_amendments
from state.fx import build_fx_table
from verify.safety import build_user_context, compute_amount_safe_to_pay, earliest_date_for_full_payment


def evaluate_set(amends_path: Path) -> dict[str, Any]:
    events = load_financial_events()
    profiles = load_financial_profiles()
    samples = load_sample_requests()
    options = load_request_payment_options()
    amends = load_message_amendments(amends_path)
    rates = load_exchange_rates()
    fx = build_fx_table(rates)

    method_matches = 0
    plan_matches = 0
    status_matches = 0
    changes_matches = 0
    safe_matches_exact = 0
    safe_matches_10pct = 0

    results: dict[str, dict[str, Any]] = {}

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
        safe_amt = compute_amount_safe_to_pay(ctx)
        earliest_dt = earliest_date_for_full_payment(ctx)
        viable_spending = enumerate_viable_spending_combinations(s.user_id, s.request_date, p, events)
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
        cands = generate_candidates(req_obj, p, options, viable_spending, safe_amt, earliest_dt)
        chosen = select_best_candidate(cands, req_obj, p, ctx)
        status = determine_affordability_status(chosen)
        plan = format_payment_plan(chosen)
        changes = format_spending_changes(chosen.spending_changes)

        m_match = chosen.method == s.recommended_payment_method
        p_match = plan == s.payment_plan
        st_match = status == s.affordability_status
        ch_match = changes == s.spending_changes_needed
        sf_exact = safe_amt == s.amount_safe_to_pay

        # 10% tolerance band check
        if s.amount_safe_to_pay == Decimal("0"):
            sf_10pct = safe_amt == Decimal("0")
        else:
            diff = abs(safe_amt - s.amount_safe_to_pay)
            sf_10pct = (diff / s.amount_safe_to_pay) <= Decimal("0.10")

        if m_match: method_matches += 1
        if p_match: plan_matches += 1
        if st_match: status_matches += 1
        if ch_match: changes_matches += 1
        if sf_exact: safe_matches_exact += 1
        if sf_10pct: safe_matches_10pct += 1

        results[s.request_id] = {
            "method": chosen.method.value,
            "plan": plan,
            "status": status.value,
            "changes": changes,
            "safe_amt": safe_amt,
            "m_match": m_match,
            "p_match": p_match,
            "st_match": st_match,
            "ch_match": ch_match,
            "sf_exact": sf_exact,
            "sf_10pct": sf_10pct,
            "gt": {
                "method": s.recommended_payment_method.value,
                "plan": s.payment_plan,
                "status": s.affordability_status.value,
                "changes": s.spending_changes_needed,
                "safe_amt": s.amount_safe_to_pay,
            }
        }

    return {
        "results": results,
        "totals": {
            "method": method_matches,
            "plan": plan_matches,
            "status": status_matches,
            "changes": changes_matches,
            "safe_exact": safe_matches_exact,
            "safe_10pct": safe_matches_10pct,
        }
    }


def compare() -> None:
    det_path = repo_root / "src" / "data" / "message_amendments.json"
    model_path = repo_root / "src" / "data" / "model_message_amendments.json"

    print("Evaluating Baseline (Deterministic)...")
    base_res = evaluate_set(det_path)

    print("Evaluating Model Extractions (Claude-Sonnet-5)...")
    model_res = evaluate_set(model_path)

    b_tot = base_res["totals"]
    m_tot = model_res["totals"]

    print("\n" + "=" * 90)
    print("CALIBRATION GUARDRAIL SUMMARY (25 Ground Truth Requests)")
    print("=" * 90)
    print(f"{'Metric':<25} | {'Baseline (Deterministic)':<25} | {'Model (claude-sonnet-5)':<25} | {'Delta'}")
    print("-" * 90)
    print(f"{'Method':<25} | {b_tot['method']:>2}/25 ({b_tot['method']/25*100:.1f}%)               | {m_tot['method']:>2}/25 ({m_tot['method']/25*100:.1f}%)               | {m_tot['method'] - b_tot['method']:+d}")
    print(f"{'Payment Plan':<25} | {b_tot['plan']:>2}/25 ({b_tot['plan']/25*100:.1f}%)               | {m_tot['plan']:>2}/25 ({m_tot['plan']/25*100:.1f}%)               | {m_tot['plan'] - b_tot['plan']:+d}")
    print(f"{'Affordability Status':<25} | {b_tot['status']:>2}/25 ({b_tot['status']/25*100:.1f}%)               | {m_tot['status']:>2}/25 ({m_tot['status']/25*100:.1f}%)               | {m_tot['status'] - b_tot['status']:+d}")
    print(f"{'Spending Changes':<25} | {b_tot['changes']:>2}/25 ({b_tot['changes']/25*100:.1f}%)               | {m_tot['changes']:>2}/25 ({m_tot['changes']/25*100:.1f}%)               | {m_tot['changes'] - b_tot['changes']:+d}")
    print(f"{'Safe Amount (Exact)':<25} | {b_tot['safe_exact']:>2}/25 ({b_tot['safe_exact']/25*100:.1f}%)               | {m_tot['safe_exact']:>2}/25 ({m_tot['safe_exact']/25*100:.1f}%)               | {m_tot['safe_exact'] - b_tot['safe_exact']:+d}")
    print(f"{'Safe Amount (<=10%)':<25} | {b_tot['safe_10pct']:>2}/25 ({b_tot['safe_10pct']/25*100:.1f}%)               | {m_tot['safe_10pct']:>2}/25 ({m_tot['safe_10pct']/25*100:.1f}%)               | {m_tot['safe_10pct'] - b_tot['safe_10pct']:+d}")
    print("=" * 90)

    print("\nROW-BY-ROW COMPARISON:")
    print(f"{'Req ID':<10} | {'Field':<18} | {'Ground Truth':<25} | {'Baseline (Deterministic)':<25} | {'Model (claude-sonnet-5)'}")
    print("-" * 110)
    for rid in base_res["results"]:
        br = base_res["results"][rid]
        mr = model_res["results"][rid]
        differs = (
            br["method"] != mr["method"]
            or br["plan"] != mr["plan"]
            or br["status"] != mr["status"]
            or br["changes"] != mr["changes"]
            or abs(br["safe_amt"] - mr["safe_amt"]) > Decimal("0.01")
        )
        flag = " *" if differs else "  "
        print(f"{rid:<8}{flag} | {'method':<18} | {br['gt']['method']:<25} | {br['method']:<25} | {mr['method']}")
        if differs:
            print(f"{'':<10} | {'plan':<18} | {br['gt']['plan']:<25} | {br['plan']:<25} | {mr['plan']}")
            print(f"{'':<10} | {'status':<18} | {br['gt']['status']:<25} | {br['status']:<25} | {mr['status']}")
            print(f"{'':<10} | {'changes':<18} | {br['gt']['changes']:<25} | {br['changes']:<25} | {mr['changes']}")
            print(f"{'':<10} | {'safe_amt':<18} | {str(br['gt']['safe_amt']):<25} | {str(br['safe_amt']):<25} | {str(mr['safe_amt'])}")
            print("-" * 110)


if __name__ == "__main__":
    compare()

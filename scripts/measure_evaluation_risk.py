"""Step 1: Measure real risk across the 250 evaluation requests between deterministic and model amendments.

Compares:
  - Deterministic amendments: src/data/message_amendments.json
  - Model amendments: src/data/model_message_amendments.json
Across all 250 requests in dataset/requests.csv.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path
import sys
from typing import Any

repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root / "src"))
sys.path.insert(0, str(repo_root))

from dataio.loaders import (
    load_exchange_rates,
    load_financial_events,
    load_financial_profiles,
    load_request_payment_options,
    load_requests,
)
from main import process_request
from models import OutputRow, RequestPaymentOption
from state.amendments import load_message_amendments
from state.fx import build_fx_table


def run_eval_pipeline(amends_path: Path) -> dict[str, OutputRow]:
    events = load_financial_events()
    events_by_id = {e.event_id: e for e in events}
    profiles = load_financial_profiles()
    requests = load_requests()
    raw_options = load_request_payment_options()
    rates = load_exchange_rates()
    fx_table = build_fx_table(rates)
    amendments = load_message_amendments(amends_path)

    options_by_req: dict[str, list[RequestPaymentOption]] = {}
    for opt in raw_options:
        options_by_req.setdefault(opt.request_id, []).append(opt)

    results: dict[str, OutputRow] = {}
    for req in requests:
        profile = profiles[req.user_id]
        row, _, _ = process_request(
            req=req,
            profile=profile,
            events=events,
            events_by_id=events_by_id,
            options_by_request=options_by_req,
            fx_table=fx_table,
            amendments=amendments,
        )
        results[req.request_id] = row
    return results


def main() -> None:
    det_path = repo_root / "src" / "data" / "message_amendments.json"
    model_path = repo_root / "src" / "data" / "model_message_amendments.json"

    print("Running 250 evaluation requests with deterministic baseline amendments...")
    det_rows = run_eval_pipeline(det_path)

    print("Running 250 evaluation requests with model amendments...")
    model_rows = run_eval_pipeline(model_path)

    total_requests = len(det_rows)
    differing_requests: list[str] = []

    field_diffs: dict[str, int] = {
        "recommended_payment_method": 0,
        "payment_plan": 0,
        "affordability_status": 0,
        "spending_changes_needed": 0,
        "amount_safe_to_pay": 0,
        "earliest_date_for_full_payment": 0,
        "decision_explanation": 0,
    }

    diff_details: list[dict[str, Any]] = []

    for req_id in sorted(det_rows.keys()):
        dr = det_rows[req_id]
        mr = model_rows[req_id]

        m_diff = dr.recommended_payment_method != mr.recommended_payment_method
        p_diff = dr.payment_plan != mr.payment_plan
        s_diff = dr.affordability_status != mr.affordability_status
        c_diff = dr.spending_changes_needed != mr.spending_changes_needed
        safe_diff = dr.amount_safe_to_pay != mr.amount_safe_to_pay
        e_diff = dr.earliest_date_for_full_payment != mr.earliest_date_for_full_payment
        exp_diff = dr.decision_explanation != mr.decision_explanation

        if m_diff: field_diffs["recommended_payment_method"] += 1
        if p_diff: field_diffs["payment_plan"] += 1
        if s_diff: field_diffs["affordability_status"] += 1
        if c_diff: field_diffs["spending_changes_needed"] += 1
        if safe_diff: field_diffs["amount_safe_to_pay"] += 1
        if e_diff: field_diffs["earliest_date_for_full_payment"] += 1
        if exp_diff: field_diffs["decision_explanation"] += 1

        any_diff = (
            m_diff
            or p_diff
            or s_diff
            or c_diff
            or safe_diff
            or e_diff
            or exp_diff
        )

        if any_diff:
            differing_requests.append(req_id)
            diff_details.append({
                "request_id": req_id,
                "m_diff": m_diff,
                "p_diff": p_diff,
                "s_diff": s_diff,
                "c_diff": c_diff,
                "safe_diff": safe_diff,
                "e_diff": e_diff,
                "det": dr,
                "model": mr,
            })

    print("\n" + "=" * 80)
    print("STEP 1: MEASURE THE REAL RISK (250 Evaluation Requests)")
    print("=" * 80)
    print(f"Total Evaluation Requests: {total_requests}")
    print(f"Total Rows Differing in ANY field: {len(differing_requests)} ({len(differing_requests)/total_requests*100:.1f}%)")
    print(f"Total Rows Completely Identical: {total_requests - len(differing_requests)} ({(total_requests - len(differing_requests))/total_requests*100:.1f}%)")
    print("-" * 80)
    print("DIFFERENCES PER FIELD:")
    for fld, cnt in field_diffs.items():
        print(f"  - {fld:<32}: {cnt:>3} / 250 ({cnt/total_requests*100:.1f}%)")
    print("=" * 80)

    print("\nITEMIZED DIFFERING REQUESTS (SIDE BY SIDE):")
    for d in diff_details:
        rid = d["request_id"]
        det_r: OutputRow = d["det"]
        mod_r: OutputRow = d["model"]
        print(f"\nRequest: {rid}")
        if d["m_diff"]:
            print(f"  method:       Deterministic: {det_r.recommended_payment_method:<18} | Model: {mod_r.recommended_payment_method}")
        if d["s_diff"]:
            print(f"  status:       Deterministic: {det_r.affordability_status:<18} | Model: {mod_r.affordability_status}")
        if d["p_diff"]:
            print(f"  plan:         Deterministic: {det_r.payment_plan:<18} | Model: {mod_r.payment_plan}")
        if d["safe_diff"]:
            print(f"  safe_to_pay:  Deterministic: {det_r.amount_safe_to_pay:<18} | Model: {mod_r.amount_safe_to_pay}")
        if d["e_diff"]:
            print(f"  earliest_dt:  Deterministic: {det_r.earliest_date_for_full_payment:<18} | Model: {mod_r.earliest_date_for_full_payment}")
        if d["c_diff"]:
            print(f"  changes:      Deterministic: {det_r.spending_changes_needed:<18} | Model: {mod_r.spending_changes_needed}")


if __name__ == "__main__":
    main()

import sys
sys.path.insert(0, 'src')
from decimal import Decimal, ROUND_DOWN, ROUND_HALF_UP
from datetime import date, timedelta
from dataio.loaders import (
    load_financial_events,
    load_financial_profiles,
    load_sample_requests,
    load_request_payment_options,
    load_exchange_rates,
)
from state.amendments import load_message_amendments
from state.fx import build_fx_table
from verify.safety import build_user_context, compute_amount_safe_to_pay, earliest_date_for_full_payment
from models import Request, Candidate, Payment, PaymentMethod
from planner.candidates import generate_candidates, format_payment_plan
from planner.spending import enumerate_viable_spending_combinations, format_spending_changes
from planner.ranking import select_best_candidate, determine_affordability_status

events = load_financial_events()
profiles = load_financial_profiles()
samples = load_sample_requests()
options = load_request_payment_options()
amends = load_message_amendments()
rates = load_exchange_rates()
fx = build_fx_table(rates)

def run_evaluation(rounding_mode):
    results = {}
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
        raw_safe = compute_amount_safe_to_pay(ctx)
        safe_amt = raw_safe.quantize(Decimal('0.01'), rounding=rounding_mode)
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
        
        results[s.request_id] = {
            "method": chosen.method,
            "plan": plan,
            "status": status,
            "changes": changes,
            "safe_amt": safe_amt,
            "method_match": chosen.method == s.recommended_payment_method,
            "plan_match": plan == s.payment_plan,
            "status_match": status == s.affordability_status,
            "changes_match": changes == s.spending_changes_needed,
            "safe_match": safe_amt == s.amount_safe_to_pay,
        }
    return results

res_up = run_evaluation(ROUND_HALF_UP)
res_down = run_evaluation(ROUND_DOWN)

print("Comparison of results (ROUND_HALF_UP vs ROUND_DOWN):")
header = f"{'request_id':<11} | {'Method (UP -> DOWN)':<32} | {'Plan moved?':<12} | {'Status moved?':<14} | {'Changes moved?':<15} | {'Safe (UP -> DOWN)':<25}"
print(header)
print('-' * len(header))

method_diffs = []
plan_diffs = []
status_diffs = []
changes_diffs = []
safe_diffs = []

for s in samples:
    rid = s.request_id
    u = res_up[rid]
    d = res_down[rid]
    
    m_diff = u["method"] != d["method"]
    p_diff = u["plan"] != d["plan"]
    st_diff = u["status"] != d["status"]
    ch_diff = u["changes"] != d["changes"]
    sf_diff = u["safe_amt"] != d["safe_amt"]
    
    if m_diff: method_diffs.append(rid)
    if p_diff: plan_diffs.append(rid)
    if st_diff: status_diffs.append(rid)
    if ch_diff: changes_diffs.append(rid)
    if sf_diff: safe_diffs.append(rid)
    
    m_str = f"{u['method'].value} -> {d['method'].value}"
    sf_str = f"{u['safe_amt']} -> {d['safe_amt']}"
    
    print(f"{rid:<11} | {m_str:<32} | {str(p_diff):<12} | {str(st_diff):<14} | {str(ch_diff):<15} | {sf_str:<25}")

print('-' * len(header))
print(f"Summary of changes with ROUND_DOWN:")
print(f"Method matches:  UP={sum(1 for r in res_up.values() if r['method_match'])}/25 -> DOWN={sum(1 for r in res_down.values() if r['method_match'])}/25")
print(f"Plan matches:    UP={sum(1 for r in res_up.values() if r['plan_match'])}/25 -> DOWN={sum(1 for r in res_down.values() if r['plan_match'])}/25")
print(f"Status matches:  UP={sum(1 for r in res_up.values() if r['status_match'])}/25 -> DOWN={sum(1 for r in res_down.values() if r['status_match'])}/25")
print(f"Changes matches: UP={sum(1 for r in res_up.values() if r['changes_match'])}/25 -> DOWN={sum(1 for r in res_down.values() if r['changes_match'])}/25")
print(f"Safe matches:    UP={sum(1 for r in res_up.values() if r['safe_match'])}/25 -> DOWN={sum(1 for r in res_down.values() if r['safe_match'])}/25")
print(f"Rows where method moved: {method_diffs}")
print(f"Rows where plan moved:   {plan_diffs}")
print(f"Rows where safe moved:   {safe_diffs}")

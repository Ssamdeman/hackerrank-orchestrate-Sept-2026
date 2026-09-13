import sys
sys.path.insert(0, "src")
from decimal import Decimal
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
from models import Request
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

method_matches = 0
plan_matches = 0
status_matches = 0
changes_matches = 0
safe_matches = 0

print(f"{'request_id':<11} | {'GT Method':<15} | {'Our Method':<15} | {'M?':<2} | {'GT Safe':<12} | {'Our Safe':<12} | {'S?':<2} | {'Status?':<7} | {'Plan?':<5} | {'Changes?':<8}")
print("-" * 105)

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
    sf_match = safe_amt == s.amount_safe_to_pay

    if m_match: method_matches += 1
    if p_match: plan_matches += 1
    if st_match: status_matches += 1
    if ch_match: changes_matches += 1
    if sf_match: safe_matches += 1

    print(f"{s.request_id:<11} | {s.recommended_payment_method.value:<15} | {chosen.method.value:<15} | {str(m_match)[0]:<2} | {str(s.amount_safe_to_pay):<12} | {str(safe_amt):<12} | {str(sf_match)[0]:<2} | {str(st_match):<7} | {str(p_match):<5} | {str(ch_match):<8}")

print("-" * 105)
print(f"Total Matches: Method={method_matches}/25, Plan={plan_matches}/25, Status={status_matches}/25, Changes={changes_matches}/25, Safe={safe_matches}/25")

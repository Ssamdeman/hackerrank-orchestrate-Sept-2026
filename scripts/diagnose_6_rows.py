import sys
sys.path.insert(0, 'src')
from datetime import timedelta
from dataio.loaders import (
    load_financial_events,
    load_financial_profiles,
    load_requests,
    load_request_payment_options,
    load_exchange_rates,
)
from state.amendments import load_message_amendments
from state.fx import build_fx_table
from verify.safety import build_user_context, compute_amount_safe_to_pay, earliest_date_for_full_payment, is_safe
from models import Candidate, Payment, PaymentMethod
from planner.candidates import generate_candidates, format_payment_plan
from planner.spending import enumerate_viable_spending_combinations, format_spending_changes
from planner.ranking import select_best_candidate, determine_affordability_status

events = load_financial_events()
profiles = load_financial_profiles()
requests = load_requests()
options = load_request_payment_options()
amends = load_message_amendments()
rates = load_exchange_rates()
fx = build_fx_table(rates)

inconsistent_ids = ['request_111', 'request_165', 'request_174', 'request_201', 'request_215', 'request_237']

for r in requests:
    if r.request_id not in inconsistent_ids:
        continue
    p = profiles[r.user_id]
    ctx = build_user_context(
        user_id=r.user_id,
        request_date=r.request_date,
        opening_balance=p.current_available_balance,
        minimum_balance_to_keep=p.minimum_balance_to_keep,
        requested_amount=r.requested_amount,
        events=events,
        amendments=amends,
        home_currency=p.home_currency,
        fx_table=fx,
        request_id=r.request_id,
    )
    safe_amt = compute_amount_safe_to_pay(ctx)
    earliest_dt_raw = earliest_date_for_full_payment(ctx)
    viable_spending = enumerate_viable_spending_combinations(r.user_id, r.request_date, p, events)
    cands = generate_candidates(r, p, options, viable_spending, safe_amt, earliest_dt_raw)
    chosen = select_best_candidate(cands, r, p, ctx)
    status = determine_affordability_status(chosen)
    plan = format_payment_plan(chosen)
    changes = format_spending_changes(chosen.spending_changes)
    
    # Check if full payment is safe on ANY date in window WITH chosen spending changes
    safe_dates_with_changes = []
    for day_offset in range(ctx.horizon_days + 1):
        cand_date = ctx.request_date + timedelta(days=day_offset)
        cand = Candidate(
            method=PaymentMethod.FULL_PAYMENT,
            payments=(Payment(date=cand_date, amount=ctx.requested_amount),),
            spending_changes=chosen.spending_changes,
            payment_option_id=None,
            total_paid=ctx.requested_amount,
        )
        res = is_safe(cand, ctx)
        if res.is_safe:
            safe_dates_with_changes.append(cand_date)
            
    earliest_with_changes = safe_dates_with_changes[0] if safe_dates_with_changes else None
    
    print(f"Request: {r.request_id}")
    print(f"  User: {r.user_id}, Currency: {p.home_currency}")
    print(f"  Request Date: {r.request_date}, Desired Date: {r.desired_completion_date}")
    print(f"  Requested Amount: {r.requested_amount}")
    print(f"  Opening Balance: {p.current_available_balance}, Min Balance: {p.minimum_balance_to_keep}")
    print(f"  Chosen Method: {chosen.method.value}")
    print(f"  Status: {status.value}")
    print(f"  Plan: {plan}")
    print(f"  Spending Changes: {changes}")
    print(f"  Safe to pay (without changes): {safe_amt}")
    print(f"  Earliest date (without changes): {earliest_dt_raw}")
    print(f"  Earliest date WITH chosen spending changes: {earliest_with_changes}")
    print(f"  Total safe dates with changes: {len(safe_dates_with_changes)}")
    print("-" * 60)

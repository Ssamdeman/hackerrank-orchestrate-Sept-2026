import sys
sys.path.insert(0, 'src')
from decimal import Decimal
from dataio.loaders import (
    load_financial_events,
    load_financial_profiles,
    load_sample_requests,
    load_exchange_rates,
)
from state.amendments import load_message_amendments
from state.fx import build_fx_table
from verify.safety import build_user_context, compute_amount_safe_to_pay

events = load_financial_events()
profiles = load_financial_profiles()
samples = load_sample_requests()
amends = load_message_amendments()
rates = load_exchange_rates()
fx = build_fx_table(rates)

within_5 = 0
within_10 = 0
within_18 = 0
exact = 0

rows_data = []

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
    safe = compute_amount_safe_to_pay(ctx)
    gt = s.amount_safe_to_pay
    diff = safe - gt
    
    if gt == Decimal('0'):
        pct_err = Decimal('0') if safe == Decimal('0') else Decimal('999')
    else:
        pct_err = abs(diff) / gt * Decimal('100')
        
    if pct_err <= Decimal('5'):
        within_5 += 1
    if pct_err <= Decimal('10'):
        within_10 += 1
    if pct_err <= Decimal('18'):
        within_18 += 1
    if diff == Decimal('0'):
        exact += 1
        
    rows_data.append((s.request_id, gt, safe, diff, pct_err))

header = f"{'request_id':<11} | {'GT Safe':<14} | {'Our Safe':<14} | {'Difference':<14} | {'% Error':<10}"
print(header)
print('-' * len(header))
for rid, gt, safe, diff, pct in rows_data:
    print(f"{rid:<11} | {str(gt):<14} | {str(safe):<14} | {str(diff):<14} | {pct:>8.2f}%")

print('-' * len(header))
print(f"Exact match:   {exact}/25 ({exact/25*100:.1f}%)")
print(f"Within 5%:     {within_5}/25 ({within_5/25*100:.1f}%)")
print(f"Within 10%:    {within_10}/25 ({within_10/25*100:.1f}%)")
print(f"Within 18%:    {within_18}/25 ({within_18/25*100:.1f}%)")

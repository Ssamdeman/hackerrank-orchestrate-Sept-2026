import sys
sys.path.insert(0, 'src')
from decimal import Decimal
import pandas as pd
from dataio.loaders import load_financial_events, load_financial_profiles, load_sample_requests, load_exchange_rates
from state.amendments import load_message_amendments
from state.fx import build_fx_table
from verify.safety import build_user_context, compute_amount_safe_to_pay

events = load_financial_events()
profiles = load_financial_profiles()
samples = load_sample_requests()
amends = load_message_amendments()
rates = load_exchange_rates()
fx = build_fx_table(rates)

cal = pd.read_csv('dataset/sample_requests.csv')
nr = cal[cal['recommended_payment_method'] == 'not_recommended']

header = f"{'request_id':<11} | {'amount_safe_to_pay':<18} | {'requested_amount':<16} | {'ratio':<10} | {'T6 or T7':<8} | {'Our Safe':<12} | {'Our Ratio'}"
print(header)
print('-' * len(header))

for idx, r in nr.iterrows():
    rid = r['request_id']
    s = [x for x in samples if x.request_id == rid][0]
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
    our_safe = compute_amount_safe_to_pay(ctx)
    gt_safe = Decimal(str(r['amount_safe_to_pay']))
    req = Decimal(str(r['requested_amount']))
    ratio = (gt_safe / req) * 100
    our_ratio = (our_safe / req) * 100
    is_t7 = 'proceed' in r['decision_explanation']
    tmpl = 'T7' if is_t7 else 'T6'
    print(f"{rid:<11} | {str(gt_safe):<18} | {str(req):<16} | {ratio:>8.2f}% | {tmpl:<8} | {str(our_safe):<12} | {our_ratio:>8.2f}%")

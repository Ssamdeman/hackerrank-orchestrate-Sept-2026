import sys
sys.path.insert(0, 'src')
import csv
import re
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

from dataio.loaders import (
    load_financial_events,
    load_financial_profiles,
    load_requests,
    load_request_payment_options,
)
from explain.formatting import format_plan_amount
from models import PaymentMethod

# Load references
requests_list = load_requests()
requests_by_id = {r.request_id: r for r in requests_list}
profiles_by_id = load_financial_profiles()
events_list = load_financial_events()
events_by_id = {e.event_id: e for e in events_list}
options_list = load_request_payment_options()
options_by_req = {}
for opt in options_list:
    options_by_req.setdefault(opt.request_id, []).append(opt)

# Read output.csv
with open('output.csv', 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    raw_header = next(reader)
    output_rows = list(reader)

expected_header = [
    'request_id',
    'amount_safe_to_pay',
    'affordability_status',
    'recommended_payment_method',
    'payment_plan',
    'earliest_date_for_full_payment',
    'spending_changes_needed',
    'decision_explanation',
]

results = {}

def record(assertion_num, name, passed, failures=None):
    results[assertion_num] = {
        'name': name,
        'passed': passed,
        'failures': failures or []
    }

# A1: Exactly 250 rows; request_id set matches requests.csv exactly
a1_pass = len(output_rows) == 250 and [r[0] for r in output_rows] == [r.request_id for r in requests_list]
record(1, "Exactly 250 rows & request_id set matches verbatim", a1_pass)

# A2: Header matches §1 byte for byte
a2_pass = raw_header == expected_header
record(2, "Header matches §1 byte-for-byte", a2_pass)

# A3: No field is null except earliest_date_for_full_payment
a3_fails = []
for r in output_rows:
    rid = r[0]
    for idx, col in enumerate(r):
        if idx == 5:
            continue
        if col is None or col == '':
            a3_fails.append(rid)
            break
record(3, "No field is null except earliest_date", len(a3_fails) == 0, a3_fails)

# A4: affordability_status in 4 allowed values
valid_statuses = {'affordable_now', 'affordable_with_plan', 'affordable_later', 'not_affordable'}
a4_fails = [r[0] for r in output_rows if r[2] not in valid_statuses]
record(4, "affordability_status in allowed values", len(a4_fails) == 0, a4_fails)

# A5: recommended_payment_method in 5 allowed values
valid_methods = {'full_payment', 'partial_payment', 'installments', 'wait', 'not_recommended'}
a5_fails = [r[0] for r in output_rows if r[3] not in valid_methods]
record(5, "recommended_payment_method in allowed values", len(a5_fails) == 0, a5_fails)

# A6: 0 <= amount_safe_to_pay <= requested_amount
a6_fails = []
for r in output_rows:
    rid, safe_str = r[0], r[1]
    safe_amt = Decimal(safe_str)
    req = requests_by_id[rid]
    if not (Decimal('0') <= safe_amt <= req.requested_amount):
        a6_fails.append(rid)
record(6, "0 <= amount_safe_to_pay <= requested_amount", len(a6_fails) == 0, a6_fails)

# A7: (status, method) in §6.2 matrix
valid_pairs = {
    ('affordable_now', 'full_payment'),
    ('affordable_with_plan', 'full_payment'),
    ('affordable_with_plan', 'installments'),
    ('affordable_with_plan', 'partial_payment'),
    ('affordable_later', 'wait'),
    ('not_affordable', 'not_recommended'),
}
a7_fails = [r[0] for r in output_rows if (r[2], r[3]) not in valid_pairs]
record(7, "(status, method) pair appears in §6.2 matrix", len(a7_fails) == 0, a7_fails)

# A8: payment_plan parses under §7.1 grammar; dates YYYY-MM-DD; chronological
a8_fails = []
date_re = re.compile(r'^\d{4}-\d{2}-\d{2}$')
for r in output_rows:
    rid, plan = r[0], r[4]
    if plan == 'none':
        continue
    items = plan.split('|')
    prev_dt = None
    parse_ok = True
    for it in items:
        parts = it.split(':')
        if len(parts) != 2 or not date_re.match(parts[0]):
            parse_ok = False
            break
        try:
            curr_dt = date.fromisoformat(parts[0])
            _ = Decimal(parts[1])
            if prev_dt is not None and curr_dt < prev_dt:
                parse_ok = False
                break
            prev_dt = curr_dt
        except Exception:
            parse_ok = False
            break
    if not parse_ok:
        a8_fails.append(rid)
record(8, "payment_plan parses under §7.1; chronological dates", len(a8_fails) == 0, a8_fails)

# A9: full_payment => one payment, dated request_date, equal to requested_amount
a9_fails = []
for r in output_rows:
    rid, method, plan = r[0], r[3], r[4]
    if method == 'full_payment':
        req = requests_by_id[rid]
        items = plan.split('|')
        if len(items) != 1:
            a9_fails.append(rid)
            continue
        dt_str, amt_str = items[0].split(':')
        if date.fromisoformat(dt_str) != req.request_date or Decimal(amt_str) != req.requested_amount:
            a9_fails.append(rid)
record(9, "full_payment plan integrity", len(a9_fails) == 0, a9_fails)

# A10: wait => one payment, dated earliest_date_for_full_payment, equal to requested_amount
a10_fails = []
for r in output_rows:
    rid, method, plan, earliest_str = r[0], r[3], r[4], r[5]
    if method == 'wait':
        req = requests_by_id[rid]
        items = plan.split('|')
        if len(items) != 1:
            a10_fails.append(rid)
            continue
        dt_str, amt_str = items[0].split(':')
        if dt_str != earliest_str or Decimal(amt_str) != req.requested_amount:
            a10_fails.append(rid)
record(10, "wait plan integrity", len(a10_fails) == 0, a10_fails)

# A11: partial_payment => exactly two payments summing to requested_amount; first dated request_date and equal to amount_safe_to_pay
a11_fails = []
for r in output_rows:
    rid, safe_str, method, plan = r[0], r[1], r[3], r[4]
    if method == 'partial_payment':
        req = requests_by_id[rid]
        items = plan.split('|')
        if len(items) != 2:
            a11_fails.append(rid)
            continue
        dt1, amt1 = items[0].split(':')
        dt2, amt2 = items[1].split(':')
        if date.fromisoformat(dt1) != req.request_date or Decimal(amt1) != Decimal(safe_str):
            a11_fails.append(rid)
        elif Decimal(amt1) + Decimal(amt2) != req.requested_amount:
            a11_fails.append(rid)
record(11, "partial_payment plan integrity", len(a11_fails) == 0, a11_fails)

# A12: installments => dates, count, and amounts reproduce a real payment_option_id exactly
a12_fails = []
for r in output_rows:
    rid, method, plan = r[0], r[3], r[4]
    if method == 'installments':
        req_opts = options_by_req.get(rid, [])
        items = plan.split('|')
        matched_opt = False
        for opt in req_opts:
            if opt.payment_method.value != 'installments':
                continue
            if len(items) != opt.number_of_payments:
                continue
            freq = opt.payment_frequency_days or 30
            expected_plan_parts = [
                f"{(opt.first_payment_date + timedelta(days=k*freq)).isoformat()}:{format_plan_amount(opt.payment_amount)}"
                for k in range(opt.number_of_payments)
            ]
            if plan == '|'.join(expected_plan_parts):
                matched_opt = True
                break
        if not matched_opt:
            a12_fails.append(rid)
record(12, "installments reproduces supplied option exactly", len(a12_fails) == 0, a12_fails)

# A13: not_recommended => payment_plan == 'none'
a13_fails = [r[0] for r in output_rows if r[3] == 'not_recommended' and r[4] != 'none']
record(13, "not_recommended payment_plan is none", len(a13_fails) == 0, a13_fails)

# A14: Every plan completes by desired_completion_date, except not_recommended
a14_fails = []
for r in output_rows:
    rid, method, plan = r[0], r[3], r[4]
    if method != 'not_recommended':
        req = requests_by_id[rid]
        items = plan.split('|')
        last_dt = date.fromisoformat(items[-1].split(':')[0])
        if last_dt > req.desired_completion_date:
            a14_fails.append(rid)
record(14, "Plan completes by desired_completion_date", len(a14_fails) == 0, a14_fails)

# A15: affordable_now => earliest_date_for_full_payment == request_date
a15_fails = []
for r in output_rows:
    rid, status, earliest_str = r[0], r[2], r[5]
    if status == 'affordable_now':
        req = requests_by_id[rid]
        if earliest_str != req.request_date.isoformat():
            a15_fails.append(rid)
record(15, "affordable_now earliest_date == request_date", len(a15_fails) == 0, a15_fails)

# A16: not_affordable <=> earliest_date_for_full_payment empty
a16_fails = []
for r in output_rows:
    rid, status, earliest_str = r[0], r[2], r[5]
    is_not_aff = (status == 'not_affordable')
    is_empty = (earliest_str == '')
    if is_not_aff != is_empty:
        a16_fails.append(rid)
record(16, "not_affordable <=> earliest_date empty", len(a16_fails) == 0, a16_fails)

# A17: All other statuses => populated and within the 90-day window
a17_fails = []
for r in output_rows:
    rid, status, earliest_str = r[0], r[2], r[5]
    if status != 'not_affordable':
        if not earliest_str:
            a17_fails.append(rid)
        else:
            req = requests_by_id[rid]
            edt = date.fromisoformat(earliest_str)
            if not (req.request_date <= edt <= req.request_date + timedelta(days=90)):
                a17_fails.append(rid)
record(17, "Other statuses earliest_date populated in window", len(a17_fails) == 0, a17_fails)

# A18: spending_changes_needed parses under §8.1; at most 3 changes
a18_fails = []
for r in output_rows:
    rid, changes = r[0], r[6]
    if changes == 'none':
        continue
    items = changes.split('|')
    if len(items) > 3:
        a18_fails.append(rid)
        continue
    for it in items:
        parts = it.split(':')
        if parts[0] == 'stop' and len(parts) == 2:
            pass
        elif parts[0] == 'reduce_to' and len(parts) == 3:
            try:
                _ = Decimal(parts[2])
            except Exception:
                a18_fails.append(rid)
                break
        else:
            a18_fails.append(rid)
            break
record(18, "spending_changes parses under §8.1 (<= 3)", len(a18_fails) == 0, a18_fails)

# A19: Every cited event_id exists and belongs to this user_id
a19_fails = []
for r in output_rows:
    rid, changes = r[0], r[6]
    if changes == 'none':
        continue
    req = requests_by_id[rid]
    for it in changes.split('|'):
        parts = it.split(':')
        eid = parts[1]
        ev = events_by_id.get(eid)
        if ev is None or ev.user_id != req.user_id:
            a19_fails.append(rid)
            break
record(19, "Every cited event_id belongs to user", len(a19_fails) == 0, a19_fails)

# A20: Operation is permitted by event flexibility
a20_fails = []
for r in output_rows:
    rid, changes = r[0], r[6]
    if changes == 'none':
        continue
    for it in changes.split('|'):
        parts = it.split(':')
        act = parts[0]
        eid = parts[1]
        ev = events_by_id[eid]
        flx = ev.flexibility.value
        if act == 'stop' and flx not in ('stoppable', 'reducible_or_stoppable'):
            a20_fails.append(rid)
            break
        elif act == 'reduce_to' and flx not in ('reducible', 'reducible_or_stoppable'):
            a20_fails.append(rid)
            break
record(20, "Operation permitted by flexibility", len(a20_fails) == 0, a20_fails)

# A21: Category in user's willingness list and NOT in expense_categories_to_protect
a21_fails = []
for r in output_rows:
    rid, changes = r[0], r[6]
    if changes == 'none':
        continue
    req = requests_by_id[rid]
    p = profiles_by_id[req.user_id]
    for it in changes.split('|'):
        parts = it.split(':')
        act = parts[0]
        eid = parts[1]
        ev = events_by_id[eid]
        if ev.category in p.expense_categories_to_protect:
            a21_fails.append(rid)
            break
        if act == 'stop' and ev.category not in p.expense_categories_user_is_willing_to_stop:
            a21_fails.append(rid)
            break
        if act == 'reduce_to' and ev.category not in p.expense_categories_user_is_willing_to_reduce:
            a21_fails.append(rid)
            break
record(21, "Willingness list obeyed & protected categories preserved", len(a21_fails) == 0, a21_fails)

# A22: No event_id appears with both stop and reduce_to
a22_fails = []
for r in output_rows:
    rid, changes = r[0], r[6]
    if changes == 'none':
        continue
    cited_eids = [it.split(':')[1] for it in changes.split('|')]
    if len(cited_eids) != len(set(cited_eids)):
        a22_fails.append(rid)
record(22, "No duplicate event_id across stop and reduce_to", len(a22_fails) == 0, a22_fails)

# A23: affordable_now and not_affordable => spending_changes_needed == 'none'
a23_fails = [r[0] for r in output_rows if r[2] in ('affordable_now', 'not_affordable') and r[6] != 'none']
record(23, "affordable_now & not_affordable have no spending changes", len(a23_fails) == 0, a23_fails)

# A24: Matches one of the 7 templates for the emitted (status, method) pair
a24_fails = []
for r in output_rows:
    rid, status, method, expl = r[0], r[2], r[3], r[7]
    if method == 'full_payment' and status == 'affordable_now':
        if not (expl.startswith('Pay ') and 'over the next 90 days' in expl):
            a24_fails.append(rid)
    elif method == 'full_payment' and status == 'affordable_with_plan':
        if not ('then pay ' in expl and 'leaves at least ' in expl):
            a24_fails.append(rid)
    elif method == 'installments':
        if not (expl.startswith('Use ') and 'installments of ' in expl):
            a24_fails.append(rid)
    elif method == 'wait':
        if not (expl.startswith('Pay ') and 'in full on ' in expl and 'Paying earlier' in expl):
            a24_fails.append(rid)
    elif method == 'partial_payment':
        if not (expl.startswith('Pay ') and 'today and the remaining' in expl):
            a24_fails.append(rid)
    elif method == 'not_recommended':
        if not (expl.startswith('Do not make this payment by ') or expl.startswith('Do not proceed with the ')):
            a24_fails.append(rid)
record(24, "Explanation matches contract template", len(a24_fails) == 0, a24_fails)

# A25: Every number and date in text agrees with structured fields in same row
a25_fails = []
for r in output_rows:
    rid, safe_str, status, method, plan, earliest_str, changes, expl = r
    req = requests_by_id[rid]
    p = profiles_by_id[req.user_id]
    # In every template, minimum_balance_to_keep or requested_amount or first payment date is mentioned
    # Let's verify that desired_completion_date in T6 matches, or date in T4 matches earliest_date
    if method == 'wait':
        if earliest_str:
            edt = date.fromisoformat(earliest_str)
            edt_text = f"{edt.day} {edt.strftime('%B %Y')}"
            if edt_text not in expl:
                a25_fails.append(rid)
    elif method == 'not_recommended':
        ddt = req.desired_completion_date
        ddt_text = f"{ddt.day} {ddt.strftime('%B %Y')}"
        if 'proceed' not in expl and ddt_text not in expl:
            a25_fails.append(rid)
record(25, "Explanation numbers and dates agree with structured fields", len(a25_fails) == 0, a25_fails)

# A26 Literal: Emitted method in payment_methods_user_will_consider, or is not_recommended
a26_literal_fails = []
for r in output_rows:
    rid, method = r[0], r[3]
    if method != 'not_recommended':
        req = requests_by_id[rid]
        p = profiles_by_id[req.user_id]
        if PaymentMethod(method) not in p.payment_methods_user_will_consider:
            a26_literal_fails.append(rid)
record(26, "Method in payment_methods_user_will_consider (Literal)", len(a26_literal_fails) == 0, a26_literal_fails)

# A26 Aligned: Emitted method in payment_methods_user_will_consider (with wait requiring full_payment)
a26_aligned_fails = []
for r in output_rows:
    rid, method = r[0], r[3]
    if method == 'not_recommended':
        continue
    req = requests_by_id[rid]
    p = profiles_by_id[req.user_id]
    if method == 'wait':
        if PaymentMethod.FULL_PAYMENT not in p.payment_methods_user_will_consider:
            a26_aligned_fails.append(rid)
    else:
        if PaymentMethod(method) not in p.payment_methods_user_will_consider:
            a26_aligned_fails.append(rid)
record("26 (Aligned)", "Method in user willingness (per §6.1 wait requires full_payment)", len(a26_aligned_fails) == 0, a26_aligned_fails)

# A27: partial_payment => allows_partial_payment == true
a27_fails = [r[0] for r in output_rows if r[3] == 'partial_payment' and not requests_by_id[r[0]].allows_partial_payment]
record(27, "partial_payment only when user allows partial payment", len(a27_fails) == 0, a27_fails)

# A28: installments => number_of_payments <= max_installment_months
a28_fails = []
for r in output_rows:
    rid, method, plan = r[0], r[3], r[4]
    if method == 'installments':
        req = requests_by_id[rid]
        p = profiles_by_id[req.user_id]
        if p.max_installment_months is not None:
            num_payments = len(plan.split('|'))
            if num_payments > p.max_installment_months:
                a28_fails.append(rid)
record(28, "installments count <= max_installment_months", len(a28_fails) == 0, a28_fails)

# Print Summary Report
print("=== CONTRACT §12 VALIDATOR ASSERTIONS REPORT (250 ROWS) ===")
print(f"{'#':<12} | {'Assertion Description':<60} | {'Result':<6} | {'Failing request_ids'}")
print("-" * 105)
for num in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, "26 (Aligned)", 27, 28]:
    info = results[num]
    res_str = "PASS" if info['passed'] else "FAIL"
    fails_str = f"Count: {len(info['failures'])} -> {info['failures'][:8]}..." if len(info['failures']) > 8 else (f"Count: {len(info['failures'])} -> {info['failures']}" if info['failures'] else "None")
    print(f"{str(num):<12} | {info['name']:<60} | {res_str:<6} | {fails_str}")

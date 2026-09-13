import pandas as pd

cal = pd.read_csv("dataset/sample_requests.csv")
out = pd.read_csv("output.csv")

print("=== CALIBRATION (25 rows) vs EVALUATION (250 rows) ===")
print("\nAffordability Status:")
header_st = f"{'Status':<25} | {'Calibration (N=25)':<20} | {'Evaluation (N=250)':<20}"
print(header_st)
print("-" * len(header_st))
cal_st = cal["affordability_status"].value_counts()
out_st = out["affordability_status"].value_counts()
all_st = sorted(set(list(cal_st.index) + list(out_st.index)))
for s in all_st:
    c_cnt = cal_st.get(s, 0)
    o_cnt = out_st.get(s, 0)
    print(f"{s:<25} | {c_cnt:>3} ({c_cnt/25*100:>5.1f}%)        | {o_cnt:>3} ({o_cnt/250*100:>5.1f}%)")

print("\nRecommended Payment Method:")
header_m = f"{'Method':<25} | {'Calibration (N=25)':<20} | {'Evaluation (N=250)':<20}"
print(header_m)
print("-" * len(header_m))
cal_m = cal["recommended_payment_method"].value_counts()
out_m = out["recommended_payment_method"].value_counts()
all_m = sorted(set(list(cal_m.index) + list(out_m.index)))
for m in all_m:
    c_cnt = cal_m.get(m, 0)
    o_cnt = out_m.get(m, 0)
    print(f"{m:<25} | {c_cnt:>3} ({c_cnt/25*100:>5.1f}%)        | {o_cnt:>3} ({o_cnt/250*100:>5.1f}%)")

cal_safe_zero = int((cal["amount_safe_to_pay"] == 0).sum())
out_safe_zero = int((out["amount_safe_to_pay"] == 0).sum())
cal_earliest_empty = int(cal["earliest_date_for_full_payment"].isna().sum())
out_earliest_empty = int(out["earliest_date_for_full_payment"].isna().sum())

print("\nBoundary Counts:")
print(f"amount_safe_to_pay == 0.00:  Calibration = {cal_safe_zero}/25 ({cal_safe_zero/25*100:.1f}%), Evaluation = {out_safe_zero}/250 ({out_safe_zero/250*100:.1f}%)")
print(f"earliest_date empty:         Calibration = {cal_earliest_empty}/25 ({cal_earliest_empty/25*100:.1f}%), Evaluation = {out_earliest_empty}/250 ({out_earliest_empty/250*100:.1f}%)")

import pandas as pd

df = pd.read_csv('dataset/sample_requests.csv')
for idx, row in df.iterrows():
    print(f"{row['request_id']}: {row['recommended_payment_method']} | {row['affordability_status']} | safe={row['amount_safe_to_pay']} | {row['decision_explanation']}")

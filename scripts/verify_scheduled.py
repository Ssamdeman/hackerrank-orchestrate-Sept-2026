"""V4: Breakdown of all 70 scheduled rows in financial_events.csv.

Question: Full breakdown of all 70 scheduled rows (ASSUMED-1: phantom-liquidity risk).
"""

from __future__ import annotations

import logging
from pathlib import Path
import sys
import pandas as pd

from observability import bind_context, init_logging


def run_verify_v4() -> None:
    init_logging()
    logger = logging.getLogger("verify_v4")

    with bind_context(stage="verify_v4"):
        logger.info("Starting V4 verification: 70 scheduled rows breakdown")
        csv_path = Path("dataset/financial_events.csv")
        if not csv_path.is_file():
            raise FileNotFoundError(f"Missing {csv_path}")

        df = pd.read_csv(csv_path)
        scheduled = df[df["status"] == "scheduled"]
        total_scheduled = len(scheduled)

        direction_counts = scheduled["direction"].value_counts().to_dict()
        dir_cat_counts = scheduled.groupby(["direction", "category"]).size().to_dict()
        unique_users = int(scheduled["user_id"].nunique())
        currency_counts = scheduled["currency"].value_counts().to_dict()
        null_amounts = int(scheduled["amount"].isna().sum())
        null_rows = scheduled[scheduled["amount"].isna()]
        sys.stdout.write(f"V4: Null amounts: {null_amounts}\n")
        if not null_rows.empty:
            for _, row in null_rows.iterrows():
                sys.stdout.write(
                    f"  - null_amount_row: event_id={row['event_id']}, user={row['user_id']}, "
                    f"dir={row['direction']}, cat={row['category']}, desc='{row['description']}'\n"
                )

        date_min = scheduled["event_date"].min()
        date_max = scheduled["event_date"].max()


        sys.stdout.write(f"V4: Total scheduled rows: {total_scheduled}\n")
        sys.stdout.write(f"V4: Unique users involved: {unique_users}\n")
        sys.stdout.write(f"V4: Null amounts: {null_amounts}\n")
        sys.stdout.write(f"V4: Date range: {date_min} to {date_max}\n")
        sys.stdout.write(f"V4: Direction counts: {direction_counts}\n")
        sys.stdout.write("V4: Direction x Category counts:\n")
        for key_obj, count in sorted(dir_cat_counts.items(), key=lambda x: str(x[0])):
            if isinstance(key_obj, tuple) and len(key_obj) >= 2:
                d_val, cat_val = str(key_obj[0]), str(key_obj[1])
            else:
                d_val, cat_val = str(key_obj), ""
            sys.stdout.write(f"  - {d_val} | {cat_val}: {count}\n")


        sys.stdout.write(f"V4: Currency counts: {currency_counts}\n")

        credits = scheduled[scheduled["direction"] == "credit"]
        sys.stdout.write(f"V4: Scheduled credits count: {len(credits)}\n")
        if not credits.empty:
            sys.stdout.write("V4: Scheduled credit rows detail:\n")
            for _, row in credits.iterrows():
                sys.stdout.write(
                    f"  - event_id={row['event_id']}, user={row['user_id']}, "
                    f"date={row['event_date']}, amount={row['amount']} {row['currency']}, "
                    f"cat={row['category']}, desc='{row['description']}'\n"
                )

        debits = scheduled[scheduled["direction"] == "debit"]
        sys.stdout.write(f"V4: Scheduled debits count: {len(debits)}\n")
        if not debits.empty:
            sys.stdout.write("V4: Scheduled debit rows detail:\n")
            for _, row in debits.iterrows():
                sys.stdout.write(
                    f"  - event_id={row['event_id']}, user={row['user_id']}, "
                    f"date={row['event_date']}, amount={row['amount']} {row['currency']}, "
                    f"cat={row['category']}, desc='{row['description']}'\n"
                )



def main() -> None:
    run_verify_v4()
    sys.exit(0)


if __name__ == "__main__":
    main()

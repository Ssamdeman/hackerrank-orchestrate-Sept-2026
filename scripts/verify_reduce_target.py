"""V1: Query minimum_allowed_amount for event_989 and event_1816.

Question: minimum_allowed_amount for event_989, event_1816 (ASSUMED-7).
"""

from __future__ import annotations

import logging
from pathlib import Path
import sys
import pandas as pd

from observability import bind_context, init_logging


def run_verify_v1() -> None:
    init_logging()
    logger = logging.getLogger("verify_v1")

    with bind_context(stage="verify_v1"):
        logger.info("Starting V1 verification: reduce_to target amount")
        csv_path = Path("dataset/financial_events.csv")
        if not csv_path.is_file():
            raise FileNotFoundError(f"Missing {csv_path}")

        df = pd.read_csv(csv_path)

        target_ids = ["event_989", "event_1816"]
        targets = df[df["event_id"].isin(target_ids)]

        sys.stdout.write(f"V1: Matched target events count: {len(targets)}\n")
        for _, row in targets.iterrows():
            sys.stdout.write(
                f"  - event_id={row['event_id']}, user_id={row['user_id']}, "
                f"date={row['event_date']}, amount={row['amount']} {row['currency']}, "
                f"dir={row['direction']}, cat={row['category']}, desc='{row['description']}', "
                f"flexibility={row['flexibility']}, minimum_allowed_amount={row['minimum_allowed_amount']}\n"
            )

        # Dataset-wide context on minimum_allowed_amount
        non_null_min = df[df["minimum_allowed_amount"].notna()]
        total_non_null = len(non_null_min)
        flex_distribution = non_null_min["flexibility"].value_counts().to_dict()

        sys.stdout.write(f"V1: Total rows with non-null minimum_allowed_amount: {total_non_null}\n")
        sys.stdout.write(f"V1: Flexibility breakdown for non-null minimum_allowed_amount: {flex_distribution}\n")


def main() -> None:
    run_verify_v1()
    sys.exit(0)


if __name__ == "__main__":
    main()

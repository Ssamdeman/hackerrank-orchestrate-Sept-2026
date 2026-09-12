"""V6: Series position of the 4 cited spending-change events.

Question: Series position of event_476, event_989, event_1815, event_1816 (ASSUMED-8).
"""

from __future__ import annotations

import logging
from pathlib import Path
import sys
import pandas as pd

from observability import bind_context, init_logging


def run_verify_v6() -> None:
    init_logging()
    logger = logging.getLogger("verify_v6")

    with bind_context(stage="verify_v6"):
        logger.info("Starting V6 verification: series position of cited events")
        csv_path = Path("dataset/financial_events.csv")
        if not csv_path.is_file():
            raise FileNotFoundError(f"Missing {csv_path}")

        df = pd.read_csv(csv_path)

        cited_ids = ["event_476", "event_989", "event_1815", "event_1816"]
        sys.stdout.write(f"V6: Target cited events: {cited_ids}\n")

        for target_id in cited_ids:
            target_rows = df[df["event_id"] == target_id]
            if target_rows.empty:
                sys.stderr.write(f"FAIL: {target_id} not found\n")
                continue

            target_row = target_rows.iloc[0]
            user_id = target_row["user_id"]
            direction = target_row["direction"]
            category = target_row["category"]
            description = target_row["description"]
            currency = target_row["currency"]

            # Match series by (user_id, direction, category, description, currency)
            series = df[
                (df["user_id"] == user_id)
                & (df["direction"] == direction)
                & (df["category"] == category)
                & (df["description"] == description)
                & (df["currency"] == currency)
            ].sort_values(by=["event_date", "settlement_date", "event_id"]).reset_index(drop=True)

            total_count = len(series)
            matches = series[series["event_id"] == target_id]
            idx_forward = int(matches.index[0]) + 1  # 1-based
            idx_reverse = total_count - idx_forward + 1

            is_latest_overall = (idx_forward == total_count)

            # Metadata-bearing occurrences: flexibility != 'fixed' or non-null minimum_allowed_amount
            meta_series = series[
                (series["flexibility"] != "fixed")
                | (series["minimum_allowed_amount"].notna())
            ]
            total_meta_count = len(meta_series)
            meta_matches = meta_series[meta_series["event_id"] == target_id]
            is_metadata_bearing = not meta_matches.empty
            is_latest_metadata_bearing = False
            meta_idx_reverse = None
            if is_metadata_bearing:
                meta_idx_forward = int(meta_matches.index[0]) + 1
                meta_idx_reverse = total_meta_count - meta_idx_forward + 1
                is_latest_metadata_bearing = (meta_idx_forward == total_meta_count)

            sys.stdout.write(
                f"V6: {target_id}:\n"
                f"  - user={user_id}, cat={category}, desc='{description}'\n"
                f"  - total_series_events={total_count}\n"
                f"  - chronological_index={idx_forward} of {total_count}\n"
                f"  - reverse_index={idx_reverse} (1 = latest)\n"
                f"  - is_latest_overall={is_latest_overall}\n"
                f"  - total_metadata_bearing_events={total_meta_count}\n"
                f"  - is_metadata_bearing={is_metadata_bearing}\n"
                f"  - is_latest_metadata_bearing={is_latest_metadata_bearing}\n"
                f"  - meta_reverse_index={meta_idx_reverse}\n"
            )


def main() -> None:
    run_verify_v6()
    sys.exit(0)


if __name__ == "__main__":
    main()

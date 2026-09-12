"""V3: Exact duplicate collision count in financial_events.csv.

Question: Exact (user_id, amount, event_date, description) collision count (ASSUMED-4; possible deletion of §3.4).
"""

from __future__ import annotations

import logging
from pathlib import Path
import sys
import pandas as pd

from observability import bind_context, init_logging


def run_verify_v3() -> None:
    init_logging()
    logger = logging.getLogger("verify_v3")

    with bind_context(stage="verify_v3"):
        logger.info("Starting V3 verification: duplicate collisions")
        csv_path = Path("dataset/financial_events.csv")
        if not csv_path.is_file():
            raise FileNotFoundError(f"Missing {csv_path}")

        df = pd.read_csv(csv_path)
        total_rows = len(df)

        key_4 = ["user_id", "amount", "event_date", "description"]
        duplicates_4 = df[df.duplicated(subset=key_4, keep=False)]
        collision_groups_4 = df.groupby(key_4).filter(lambda g: len(g) > 1)
        num_collision_groups_4 = df.groupby(key_4).ngroups - df.drop_duplicates(subset=key_4).shape[0] # or count groups > 1

        grouped_4 = df.groupby(key_4)
        groups_gt_1 = [name for name, grp in grouped_4 if len(grp) > 1]

        key_6 = ["user_id", "amount", "event_date", "description", "direction", "currency"]
        grouped_6 = df.groupby(key_6)
        groups_gt_1_6 = [name for name, grp in grouped_6 if len(grp) > 1]

        sys.stdout.write(f"V3: Total events inspected: {total_rows}\n")
        sys.stdout.write(f"V3: Collision groups on (user_id, amount, event_date, description): {len(groups_gt_1)}\n")
        sys.stdout.write(f"V3: Total colliding rows on (user_id, amount, event_date, description): {len(duplicates_4)}\n")
        sys.stdout.write(f"V3: Collision groups on (user_id, amount, event_date, description, direction, currency): {len(groups_gt_1_6)}\n")
        sys.stdout.write(f"V3: Total colliding rows on 6-field key: {len(df[df.duplicated(subset=key_6, keep=False)])}\n")

        if groups_gt_1:
            sys.stdout.write("V3: Colliding groups detail:\n")
            for grp_key in groups_gt_1:
                sub = df[(df["user_id"] == grp_key[0]) & (df["amount"] == grp_key[1]) & (df["event_date"] == grp_key[2]) & (df["description"] == grp_key[3])]
                sys.stdout.write(f"  - Key: {grp_key}, Rows: {len(sub)}\n")
                for _, r in sub.iterrows():
                    sys.stdout.write(f"    * event_id={r['event_id']}, status={r['status']}, dir={r['direction']}, cat={r['category']}\n")


def main() -> None:
    run_verify_v3()
    sys.exit(0)


if __name__ == "__main__":
    main()

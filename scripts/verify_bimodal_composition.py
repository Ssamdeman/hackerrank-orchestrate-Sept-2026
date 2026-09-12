"""V8: Composition analysis of bimodal series keys.

Question: What is the composition and nature of the 231 bimodal series identified in V5?
Audits category, direction, subscription/salary status, and flexibility across bimodal series.
"""

from __future__ import annotations

from collections import Counter
import logging
from pathlib import Path
import sys
from typing import Any
import pandas as pd

from observability import bind_context, init_logging


def run_verify_v8() -> None:
    init_logging()
    logger = logging.getLogger("verify_v8")

    with bind_context(stage="verify_v8"):
        logger.info("Starting V8 verification: composition of bimodal series")
        csv_path = Path("dataset/financial_events.csv")
        if not csv_path.is_file():
            raise FileNotFoundError(f"Missing {csv_path}")

        df = pd.read_csv(csv_path)
        df["event_date"] = pd.to_datetime(df["event_date"])

        key_cols = ["user_id", "direction", "category", "description", "currency"]
        grouped = df.groupby(key_cols)

        bimodal_groups: list[tuple[Any, pd.DataFrame, dict[str, int], list[int]]] = []

        for key, group in grouped:
            n = len(group)
            if n < 3:
                continue

            sorted_dates = group["event_date"].sort_values()
            gaps = sorted_dates.diff().dropna().dt.days.tolist()

            distinct_gap_clusters: Counter[str] = Counter()
            for g in gaps:
                if g <= 4:
                    distinct_gap_clusters["daily"] += 1
                elif 5 <= g <= 10:
                    distinct_gap_clusters["weekly"] += 1
                elif 11 <= g <= 18:
                    distinct_gap_clusters["biweekly"] += 1
                elif 25 <= g <= 35:
                    distinct_gap_clusters["monthly"] += 1
                elif 55 <= g <= 65:
                    distinct_gap_clusters["bimonthly"] += 1
                elif 85 <= g <= 95:
                    distinct_gap_clusters["quarterly"] += 1
                else:
                    distinct_gap_clusters["irregular"] += 1

            multi_modes = [k for k, count in distinct_gap_clusters.items() if count >= 2]
            if len(multi_modes) >= 2:
                bimodal_groups.append((key, group, dict(distinct_gap_clusters), gaps))

        total_bimodal = len(bimodal_groups)
        sys.stdout.write(f"V8: Total bimodal series identified: {total_bimodal}\n")

        # Aggregate event-level and series-level metrics
        bimodal_event_count = sum(len(g) for _, g, _, _ in bimodal_groups)
        sys.stdout.write(f"V8: Total events in bimodal series: {bimodal_event_count}\n")

        # Series-level distributions
        category_counts: Counter[str] = Counter()
        direction_counts: Counter[str] = Counter()
        dir_cat_counts: Counter[str] = Counter()
        flexibility_counts: Counter[str] = Counter()
        mode_pair_counts: Counter[str] = Counter()
        is_subscription_or_salary = 0
        has_controllable = 0

        for key, group, modes, _ in bimodal_groups:
            direction = str(key[1])
            category = str(key[2])
            direction_counts[direction] += 1
            category_counts[category] += 1
            dir_cat_counts[f"{direction} | {category}"] += 1

            # Mode pairs
            active_modes = sorted([m for m, c in modes.items() if c >= 2])
            mode_pair_str = " + ".join(active_modes)
            mode_pair_counts[mode_pair_str] += 1

            # Check if any event has subscription type or category is salary
            types = set(group["event_type"].dropna().unique())
            flexibilities = set(group["flexibility"].dropna().unique())

            for flex in flexibilities:
                flexibility_counts[str(flex)] += 1

            if "subscription" in types or category == "salary":
                is_subscription_or_salary += 1

            if any(f != "fixed" for f in flexibilities):
                has_controllable += 1

        sys.stdout.write("\nV8: Direction distribution across bimodal series:\n")
        for d, c in direction_counts.most_common():
            sys.stdout.write(f"  - {d}: {c}\n")

        sys.stdout.write("\nV8: Direction x Category distribution across bimodal series:\n")
        for dc, c in dir_cat_counts.most_common():
            sys.stdout.write(f"  - {dc}: {c}\n")

        sys.stdout.write("\nV8: Mode cluster pairs across bimodal series:\n")
        for mp, c in mode_pair_counts.most_common():
            sys.stdout.write(f"  - {mp}: {c}\n")

        sys.stdout.write("\nV8: Flexibility representation across bimodal series:\n")
        for f, c in flexibility_counts.most_common():
            sys.stdout.write(f"  - {f}: {c}\n")

        sys.stdout.write(f"\nV8: Series with event_type == 'subscription' or category == 'salary': {is_subscription_or_salary} of {total_bimodal}\n")
        sys.stdout.write(f"V8: Series with any controllable event (flexibility != 'fixed'): {has_controllable} of {total_bimodal}\n")


def main() -> None:
    run_verify_v8()
    sys.exit(0)


if __name__ == "__main__":
    main()

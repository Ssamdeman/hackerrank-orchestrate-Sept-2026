"""V9: Analysis of sub-threshold series keys (< 3 events).

Question: What is the distribution and composition of the 3,492 sub-threshold series (< 3 events)?
Audits count == 1 vs count == 2, gap distributions, flexibility, subscription/salary status,
and cross-references cited spending-change events from sample_requests.csv.
"""

from __future__ import annotations

from collections import Counter
import logging
from pathlib import Path
import sys
from typing import Any
import pandas as pd

from observability import bind_context, init_logging


def run_verify_v9() -> None:
    init_logging()
    logger = logging.getLogger("verify_v9")

    with bind_context(stage="verify_v9"):
        logger.info("Starting V9 verification: sub-threshold series (< 3 events)")
        events_path = Path("dataset/financial_events.csv")
        samples_path = Path("dataset/sample_requests.csv")
        if not events_path.is_file():
            raise FileNotFoundError(f"Missing {events_path}")

        df = pd.read_csv(events_path)
        df["event_date"] = pd.to_datetime(df["event_date"])

        key_cols = ["user_id", "direction", "category", "description", "currency"]
        grouped = df.groupby(key_cols)

        total_series = len(grouped)
        series_ge_3 = 0
        series_1: list[tuple[Any, pd.DataFrame]] = []
        series_2: list[tuple[Any, pd.DataFrame, int]] = []

        # Map event_id to series size and series key
        event_to_series_size: dict[str, int] = {}
        event_to_key: dict[str, Any] = {}

        for key, group in grouped:
            n = len(group)
            for eid in group["event_id"]:
                event_to_series_size[str(eid)] = n
                event_to_key[str(eid)] = key

            if n >= 3:
                series_ge_3 += 1
            elif n == 1:
                series_1.append((key, group))
            elif n == 2:
                sorted_dates = group["event_date"].sort_values()
                gap = int((sorted_dates.iloc[1] - sorted_dates.iloc[0]).days)
                series_2.append((key, group, gap))

        total_subthreshold = len(series_1) + len(series_2)
        sys.stdout.write(f"V9: Total series keys: {total_series}\n")
        sys.stdout.write(f"V9: Series >= 3 events: {series_ge_3}\n")
        sys.stdout.write(f"V9: Total sub-threshold series (< 3 events): {total_subthreshold}\n")
        sys.stdout.write(f"  - Count == 1: {len(series_1)}\n")
        sys.stdout.write(f"  - Count == 2: {len(series_2)}\n")

        # Analysis of Count == 2 series
        s2_gaps = [gap for _, _, gap in series_2]
        s2_gap_series = pd.Series(s2_gaps)
        sys.stdout.write("\nV9: Count == 2 gap distribution (days between the 2 events):\n")
        sys.stdout.write(f"  - Min: {s2_gap_series.min()}\n")
        sys.stdout.write(f"  - Median: {s2_gap_series.median()}\n")
        sys.stdout.write(f"  - Mean: {s2_gap_series.mean():.1f}\n")
        sys.stdout.write(f"  - Max: {s2_gap_series.max()}\n")

        s2_cadence_clusters: Counter[str] = Counter()
        for g in s2_gaps:
            if g <= 4:
                s2_cadence_clusters["<= 4d (daily)"] += 1
            elif 5 <= g <= 10:
                s2_cadence_clusters["5-10d (~weekly)"] += 1
            elif 11 <= g <= 18:
                s2_cadence_clusters["11-18d (~biweekly)"] += 1
            elif 25 <= g <= 35:
                s2_cadence_clusters["25-35d (~monthly)"] += 1
            elif 55 <= g <= 65:
                s2_cadence_clusters["55-65d (~bimonthly)"] += 1
            elif 85 <= g <= 95:
                s2_cadence_clusters["85-95d (~quarterly)"] += 1
            else:
                s2_cadence_clusters["other gap"] += 1

        for cluster, cnt in s2_cadence_clusters.most_common():
            sys.stdout.write(f"  - {cluster}: {cnt}\n")

        # Flexibility and Type breakdown for Count == 2
        s2_flex_counts: Counter[str] = Counter()
        s2_cat_counts: Counter[str] = Counter()
        s2_is_sub_or_salary = 0
        s2_controllable = 0

        for key, group, _ in series_2:
            category = str(key[2])
            s2_cat_counts[category] += 1
            types = set(group["event_type"].dropna().unique())
            flexibilities = set(group["flexibility"].dropna().unique())
            for f in flexibilities:
                s2_flex_counts[str(f)] += 1
            if "subscription" in types or category == "salary":
                s2_is_sub_or_salary += 1
            if any(f != "fixed" for f in flexibilities):
                s2_controllable += 1

        sys.stdout.write(f"\nV9: Count == 2 with subscription type or salary category: {s2_is_sub_or_salary} of {len(series_2)}\n")
        sys.stdout.write(f"V9: Count == 2 with controllable events (flexibility != 'fixed'): {s2_controllable} of {len(series_2)}\n")
        sys.stdout.write("V9: Count == 2 flexibility representation:\n")
        for f, cnt in s2_flex_counts.most_common():
            sys.stdout.write(f"  - {f}: {cnt}\n")
        sys.stdout.write("V9: Count == 2 top categories:\n")
        for cat, cnt in s2_cat_counts.most_common(5):
            sys.stdout.write(f"  - {cat}: {cnt}\n")

        # Analysis of Count == 1 series
        s1_flex_counts: Counter[str] = Counter()
        s1_cat_counts: Counter[str] = Counter()
        s1_is_sub_or_salary = 0
        s1_controllable = 0

        for key, group in series_1:
            category = str(key[2])
            s1_cat_counts[category] += 1
            types = set(group["event_type"].dropna().unique())
            flexibilities = set(group["flexibility"].dropna().unique())
            for f in flexibilities:
                s1_flex_counts[str(f)] += 1
            if "subscription" in types or category == "salary":
                s1_is_sub_or_salary += 1
            if any(f != "fixed" for f in flexibilities):
                s1_controllable += 1

        sys.stdout.write(f"\nV9: Count == 1 with subscription type or salary category: {s1_is_sub_or_salary} of {len(series_1)}\n")
        sys.stdout.write(f"V9: Count == 1 with controllable events (flexibility != 'fixed'): {s1_controllable} of {len(series_1)}\n")
        sys.stdout.write("V9: Count == 1 top categories:\n")
        for cat, cnt in s1_cat_counts.most_common(5):
            sys.stdout.write(f"  - {cat}: {cnt}\n")

        # Cross-reference with cited spending changes in sample_requests.csv
        if samples_path.is_file():
            samples_df = pd.read_csv(samples_path)
            cited_events: list[str] = []
            for col in ["spending_change_events", "cited_event_ids", "discretionary_events_to_reduce", "events_to_stop"]:
                if col in samples_df.columns:
                    for val in samples_df[col].dropna():
                        for item in str(val).split("|"):
                            clean = item.strip()
                            if clean and clean.startswith("event_"):
                                cited_events.append(clean)

            # Also check V6 specific events: event_476, event_989, event_1815, event_1816
            v6_targets = ["event_476", "event_989", "event_1815", "event_1816"]
            for vt in v6_targets:
                if vt not in cited_events:
                    cited_events.append(vt)

            cited_events = sorted(set(cited_events))
            sys.stdout.write(f"\nV9: Cross-referencing {len(cited_events)} cited spending-change events against series length:\n")
            cited_in_subthreshold: list[tuple[str, int, Any]] = []
            for eid in cited_events:
                sz = event_to_series_size.get(eid, 0)
                if sz < 3:
                    cited_in_subthreshold.append((eid, sz, event_to_key.get(eid)))

            sys.stdout.write(f"  - Cited events in series >= 3: {len(cited_events) - len(cited_in_subthreshold)}\n")
            sys.stdout.write(f"  - Cited events in sub-threshold series (< 3): {len(cited_in_subthreshold)}\n")
            for eid, sz, k in cited_in_subthreshold:
                sys.stdout.write(f"    * {eid}: series size = {sz}, key = {k}\n")


def main() -> None:
    run_verify_v9()
    sys.exit(0)


if __name__ == "__main__":
    main()

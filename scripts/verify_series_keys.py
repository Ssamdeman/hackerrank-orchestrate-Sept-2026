"""V5: Count of series keys with bimodal event_date gaps.

Question: Count of series keys with bimodal event_date gaps (§4.1 key sufficiency).
"""

from __future__ import annotations

from collections import Counter
import logging
from pathlib import Path
import sys
import pandas as pd

from observability import bind_context, init_logging


def run_verify_v5() -> None:
    init_logging()
    logger = logging.getLogger("verify_v5")

    with bind_context(stage="verify_v5"):
        logger.info("Starting V5 verification: bimodal event_date gaps in series")
        csv_path = Path("dataset/financial_events.csv")
        if not csv_path.is_file():
            raise FileNotFoundError(f"Missing {csv_path}")

        df = pd.read_csv(csv_path)
        df["event_date"] = pd.to_datetime(df["event_date"])

        key_cols = ["user_id", "direction", "category", "description", "currency"]
        grouped = df.groupby(key_cols)

        total_series = len(grouped)
        series_ge_3 = 0
        bimodal_series: list[dict[str, object]] = []

        cadence_counts: Counter[str] = Counter()

        for key, group in grouped:
            n = len(group)
            if n < 3:
                continue
            series_ge_3 += 1

            sorted_dates = group["event_date"].sort_values()
            gaps = sorted_dates.diff().dropna().dt.days.tolist()

            median_gap = pd.Series(gaps).median()
            if 6 <= median_gap <= 8:
                cadence = "weekly (~7d)"
            elif 13 <= median_gap <= 16:
                cadence = "biweekly (~14d)"
            elif 27 <= median_gap <= 32:
                cadence = "monthly (~30d)"
            elif median_gap <= 3:
                cadence = "daily (<=3d)"
            else:
                cadence = f"other ({median_gap}d)"
            cadence_counts[cadence] += 1

            # Check for bimodal gaps:
            # A series has bimodal gaps if it exhibits two distinct gap sizes (e.g. ~7d and ~30d)
            # where both cluster modes have significant representation.
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

            # If at least two different cadences have >= 2 gaps each
            multi_modes = [k for k, count in distinct_gap_clusters.items() if count >= 2]
            if len(multi_modes) >= 2:
                bimodal_series.append({
                    "key": key,
                    "event_count": n,
                    "gaps": gaps,
                    "modes": dict(distinct_gap_clusters),
                })

        sys.stdout.write(f"V5: Total series defined by key: {total_series}\n")
        sys.stdout.write(f"V5: Series with >= 3 events: {series_ge_3}\n")
        sys.stdout.write(f"V5: Series with < 3 events: {total_series - series_ge_3}\n")
        sys.stdout.write(f"V5: Median cadence distribution (for series >= 3):\n")
        for cad, cnt in sorted(cadence_counts.items(), key=lambda x: -x[1]):
            sys.stdout.write(f"  - {cad}: {cnt}\n")

        sys.stdout.write(f"V5: Count of series keys with bimodal event_date gaps: {len(bimodal_series)} of {series_ge_3} ({len(bimodal_series)/series_ge_3*100:.1f}%)\n")
        if bimodal_series:
            sys.stdout.write(f"V5: Showing first 10 of {len(bimodal_series)} bimodal series:\n")
            for item in bimodal_series[:10]:
                sys.stdout.write(f"  - key={item['key']}, count={item['event_count']}, modes={item['modes']}, gaps={item['gaps']}\n")



def main() -> None:
    run_verify_v5()
    sys.exit(0)


if __name__ == "__main__":
    main()

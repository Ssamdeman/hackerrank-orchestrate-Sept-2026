"""V10: Detailed analysis of the 12 bimodal credit/salary series keys.

Question: What is the exact composition, gap structure, message linkage,
and forward schedule status of the 12 bimodal salary series identified in V5/V8?
"""

from __future__ import annotations

from collections import Counter
import logging
from pathlib import Path
import sys
from typing import Any
import pandas as pd

from observability import bind_context, init_logging


def run_verify_v10() -> None:
    init_logging()
    logger = logging.getLogger("verify_v10")

    with bind_context(stage="verify_v10"):
        logger.info("Starting V10 verification: bimodal salary series analysis")
        events_path = Path("dataset/financial_events.csv")
        messages_path = Path("dataset/messages.csv")

        if not events_path.is_file():
            raise FileNotFoundError(f"Missing {events_path}")
        if not messages_path.is_file():
            raise FileNotFoundError(f"Missing {messages_path}")

        events = pd.read_csv(events_path)
        messages = pd.read_csv(messages_path)

        events["event_date"] = pd.to_datetime(events["event_date"])

        key_cols = ["user_id", "direction", "category", "description", "currency"]
        grouped = events.groupby(key_cols)

        bimodal_salary_series: list[dict[str, Any]] = []

        for key, group in grouped:
            if len(group) < 3:
                continue
            if key[1] != "credit" or key[2] != "salary":
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
                uid = str(key[0])
                desc = str(key[3])
                curr = str(key[4])
                
                # Check user messages
                user_msgs = messages[messages["user_id"] == uid]
                # Check forward scheduled events
                user_events = events[events["user_id"] == uid]
                sched = user_events[user_events["status"] == "scheduled"]
                sched_salary = sched[sched["category"] == "salary"]

                bimodal_salary_series.append({
                    "user_id": uid,
                    "description": desc,
                    "currency": curr,
                    "event_count": len(group),
                    "gaps": gaps,
                    "clusters": dict(distinct_gap_clusters),
                    "modes": sorted(multi_modes),
                    "message_count": len(user_msgs),
                    "message_source_types": user_msgs["source_type"].tolist() if not user_msgs.empty else [],
                    "scheduled_events": len(sched),
                    "scheduled_salary": len(sched_salary),
                })

        sys.stdout.write(f"V10: Total bimodal salary series: {len(bimodal_salary_series)}\n")
        unique_users = sorted(set(s["user_id"] for s in bimodal_salary_series))
        sys.stdout.write(f"V10: Unique users involved: {len(unique_users)} ({', '.join(unique_users)})\n")

        desc_counts = Counter(s["description"] for s in bimodal_salary_series)
        sys.stdout.write("V10: Description breakdown:\n")
        for d, c in desc_counts.most_common():
            sys.stdout.write(f"  - {d}: {c}\n")

        curr_counts = Counter(s["currency"] for s in bimodal_salary_series)
        sys.stdout.write("V10: Currency breakdown:\n")
        for cu, c in curr_counts.most_common():
            sys.stdout.write(f"  - {cu}: {c}\n")

        mode_pair_counts = Counter(" + ".join(s["modes"]) for s in bimodal_salary_series)
        sys.stdout.write("V10: Mode pair combinations:\n")
        for mp, c in mode_pair_counts.most_common():
            sys.stdout.write(f"  - {mp}: {c}\n")

        total_sched_salary = sum(s["scheduled_salary"] for s in bimodal_salary_series)
        sys.stdout.write(f"V10: Total forward scheduled salary rows for these users: {total_sched_salary}\n")

        total_msgs = sum(s["message_count"] for s in bimodal_salary_series)
        sys.stdout.write(f"V10: Total messages linked to these users: {total_msgs}\n")
        msg_sources: Counter[str] = Counter()
        for s in bimodal_salary_series:
            for st in s["message_source_types"]:
                msg_sources[st] += 1
        sys.stdout.write("V10: Message source_type distribution:\n")
        for st, c in msg_sources.most_common():
            sys.stdout.write(f"  - {st}: {c}\n")


if __name__ == "__main__":
    run_verify_v10()

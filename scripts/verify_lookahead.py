"""V2: Check whether event history extends past request_date.

Question: Does event history extend past request_date? (Lookahead legitimacy vs leakage).
"""

from __future__ import annotations

from collections import Counter
import logging
from pathlib import Path
import sys
import pandas as pd

from observability import bind_context, init_logging


def audit_lookahead(requests_df: pd.DataFrame, events_df: pd.DataFrame, label: str) -> None:
    merged = pd.merge(
        requests_df[["request_id", "user_id", "request_date"]],
        events_df[["event_id", "user_id", "event_date", "settlement_date", "status", "direction", "amount"]],
        on="user_id",
        how="inner",
    )

    merged["event_date"] = pd.to_datetime(merged["event_date"])
    merged["settlement_date_dt"] = pd.to_datetime(merged["settlement_date"])
    merged["request_date"] = pd.to_datetime(merged["request_date"])

    future_event_date = merged[merged["event_date"] > merged["request_date"]]
    future_settlement_date = merged[merged["settlement_date_dt"] > merged["request_date"]]

    sys.stdout.write(f"V2 ({label}): Total request-event pairs: {len(merged)}\n")
    sys.stdout.write(f"V2 ({label}): Events with event_date > request_date: {len(future_event_date)}\n")
    if not future_event_date.empty:
        status_counts = future_event_date["status"].value_counts().to_dict()
        dir_counts = future_event_date["direction"].value_counts().to_dict()
        sys.stdout.write(f"  - Status breakdown of future event_date: {status_counts}\n")
        sys.stdout.write(f"  - Direction breakdown of future event_date: {dir_counts}\n")

    sys.stdout.write(f"V2 ({label}): Events with settlement_date > request_date: {len(future_settlement_date)}\n")
    if not future_settlement_date.empty:
        status_counts_settle = future_settlement_date["status"].value_counts().to_dict()
        dir_counts_settle = future_settlement_date["direction"].value_counts().to_dict()
        sys.stdout.write(f"  - Status breakdown of future settlement_date: {status_counts_settle}\n")
        sys.stdout.write(f"  - Direction breakdown of future settlement_date: {dir_counts_settle}\n")

    # Also check if any event_date == request_date
    same_date = merged[merged["event_date"] == merged["request_date"]]
    sys.stdout.write(f"V2 ({label}): Events with event_date == request_date: {len(same_date)}\n")


def run_verify_v2() -> None:
    init_logging()
    logger = logging.getLogger("verify_v2")

    with bind_context(stage="verify_v2"):
        logger.info("Starting V2 verification: history lookahead past request_date")
        events_path = Path("dataset/financial_events.csv")
        req_path = Path("dataset/requests.csv")
        sample_path = Path("dataset/sample_requests.csv")

        events_df = pd.read_csv(events_path)
        requests_df = pd.read_csv(req_path)
        sample_df = pd.read_csv(sample_path)

        sys.stdout.write("=== V2: Evaluation Requests (250 rows) ===\n")
        audit_lookahead(requests_df, events_df, "requests.csv")

        sys.stdout.write("\n=== V2: Calibration Requests (25 rows) ===\n")
        audit_lookahead(sample_df, events_df, "sample_requests.csv")


def main() -> None:
    run_verify_v2()
    sys.exit(0)


if __name__ == "__main__":
    main()

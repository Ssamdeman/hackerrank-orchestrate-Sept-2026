"""Strict, validated CSV writer for output.csv.

Governed by docs/decision_contract.md §1 and §12.
Writes submission output.csv with exact byte-for-byte header and RFC 4180 compliance.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Sequence

from models import OutputRow

HEADER: list[str] = [
    "request_id",
    "amount_safe_to_pay",
    "affordability_status",
    "recommended_payment_method",
    "payment_plan",
    "earliest_date_for_full_payment",
    "spending_changes_needed",
    "decision_explanation",
]

HEADER_LINE: str = ",".join(HEADER)


def write_output_csv(rows: Sequence[OutputRow], path: Path | str = "output.csv") -> None:
    """Write output rows to CSV matching contract §1 byte-for-byte.

    Invariants:
      - Header matches §1 verbatim.
      - Exactly 250 rows expected on full evaluation run.
      - earliest_date_for_full_payment empty string iff not_affordable.
      - No other field may be empty or None.
    """
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(HEADER)

        for r in rows:
            if r.amount_safe_to_pay is None:
                raise ValueError(f"Missing amount_safe_to_pay for {r.request_id}")
            if r.affordability_status is None:
                raise ValueError(f"Missing affordability_status for {r.request_id}")
            if r.recommended_payment_method is None:
                raise ValueError(f"Missing recommended_payment_method for {r.request_id}")
            if r.payment_plan is None:
                raise ValueError(f"Missing payment_plan for {r.request_id}")
            if r.spending_changes_needed is None:
                raise ValueError(f"Missing spending_changes_needed for {r.request_id}")
            if r.decision_explanation is None:
                raise ValueError(f"Missing decision_explanation for {r.request_id}")

            earliest_dt_str = r.earliest_date_for_full_payment if r.earliest_date_for_full_payment is not None else ""
            if r.affordability_status == "not_affordable":
                earliest_dt_str = ""

            writer.writerow([
                r.request_id,
                r.amount_safe_to_pay,
                r.affordability_status,
                r.recommended_payment_method,
                r.payment_plan,
                earliest_dt_str,
                r.spending_changes_needed,
                r.decision_explanation,
            ])

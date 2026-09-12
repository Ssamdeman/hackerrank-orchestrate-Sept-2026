"""V7: Audit request_text for amounts, dates, and method language.

Question: request_text audit — amounts, dates, method language (§4.13).
"""

from __future__ import annotations

from collections import Counter
import logging
from pathlib import Path
import re
import sys
import pandas as pd

from observability import bind_context, init_logging


def audit_request_text(df: pd.DataFrame, label: str) -> None:
    total = len(df)
    amounts_found = 0
    amounts_diff_from_requested = 0
    diff_amount_details: list[dict[str, object]] = []

    date_patterns = [
        re.compile(r"\b\d{4}-\d{2}-\d{2}\b"),
        re.compile(r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\b", re.I),
        re.compile(r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b", re.I),
        re.compile(r"\b\d{1,2}(?:st|nd|rd|th)?\s+(?:of\s+)?(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|October|November|December)\b", re.I),
    ]

    method_keywords = {
        "installment": re.compile(r"\b(?:installment|installments|monthly|split|spread)\b", re.I),
        "full_payment": re.compile(r"\b(?:full|single payment|all at once|pay now|today)\b", re.I),
        "partial_payment": re.compile(r"\b(?:partial|part of|down payment)\b", re.I),
        "wait": re.compile(r"\b(?:wait|later|delay|postpone)\b", re.I),
    }

    dates_mentioned_count = 0
    keyword_counts: Counter[str] = Counter()

    for _, row in df.iterrows():
        text = str(row["request_text"])
        req_amt = float(row["requested_amount"])

        # Extract amounts: currency symbols or numbers
        # Find numbers >= 1
        raw_nums = re.findall(r"\b\d+(?:,\d{3})*(?:\.\d+)?\b", text)
        clean_nums: list[float] = []
        for n in raw_nums:
            val = float(n.replace(",", ""))
            if val >= 1.0:
                clean_nums.append(val)

        if clean_nums:
            amounts_found += 1
            # Check if any extracted number matches requested_amount
            matches_req = any(abs(n - req_amt) < 0.01 for n in clean_nums)
            if not matches_req:
                amounts_diff_from_requested += 1
                diff_amount_details.append({
                    "request_id": row["request_id"],
                    "requested_amount": req_amt,
                    "extracted_numbers": clean_nums,
                    "text": text,
                })

        # Check dates
        has_date = any(pat.search(text) for pat in date_patterns)
        if has_date:
            dates_mentioned_count += 1

        # Check method keywords
        for kw, pat in method_keywords.items():
            if pat.search(text):
                keyword_counts[kw] += 1

    sys.stdout.write(f"V7 ({label}): Total requests audited: {total}\n")
    sys.stdout.write(f"V7 ({label}): Requests containing numeric amounts: {amounts_found} ({amounts_found/total*100:.1f}%)\n")
    sys.stdout.write(f"V7 ({label}): Requests with numeric amounts differing from requested_amount: {amounts_diff_from_requested}\n")
    sys.stdout.write(f"V7 ({label}): Requests mentioning dates/months: {dates_mentioned_count} ({dates_mentioned_count/total*100:.1f}%)\n")
    sys.stdout.write(f"V7 ({label}): Method keyword occurrences in text:\n")
    for kw, cnt in sorted(keyword_counts.items()):
        sys.stdout.write(f"  - {kw}: {cnt} ({cnt/total*100:.1f}%)\n")

    if diff_amount_details:
        sys.stdout.write(f"V7 ({label}): Sample differing amount texts (first 5):\n")
        for item in diff_amount_details[:5]:
            sys.stdout.write(f"  - req={item['request_id']}, requested={item['requested_amount']}, nums={item['extracted_numbers']}, text='{item['text']}'\n")


def run_verify_v7() -> None:
    init_logging()
    logger = logging.getLogger("verify_v7")

    with bind_context(stage="verify_v7"):
        logger.info("Starting V7 verification: request_text audit")
        req_path = Path("dataset/requests.csv")
        sample_path = Path("dataset/sample_requests.csv")

        requests_df = pd.read_csv(req_path)
        sample_df = pd.read_csv(sample_path)

        sys.stdout.write("=== V7: Evaluation Requests (250 rows) ===\n")
        audit_request_text(requests_df, "requests.csv")

        sys.stdout.write("\n=== V7: Calibration Requests (25 rows) ===\n")
        audit_request_text(sample_df, "sample_requests.csv")


def main() -> None:
    run_verify_v7()
    sys.exit(0)


if __name__ == "__main__":
    main()

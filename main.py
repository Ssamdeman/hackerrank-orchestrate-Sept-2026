"""Main entry point for Buy or Wait financial affordability engine.

Orchestrates the full pipeline across all 250 evaluation requests:
  Load -> State / Recurrence -> Forecast -> Generate -> Test -> Rank -> Explain -> Write output.csv.
"""

from __future__ import annotations

import argparse
from datetime import date
from decimal import Decimal
from pathlib import Path
import sys
from typing import Sequence

# Add src to sys.path if not present
_SRC_DIR = Path(__file__).resolve().parent / "src"
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from dataio.loaders import (
    load_exchange_rates,
    load_financial_events,
    load_financial_profiles,
    load_request_payment_options,
    load_requests,
)
from dataio.writer import write_output_csv
from explain.formatting import format_plan_amount
from explain.templates import render_decision_explanation
from models import (
    AffordabilityStatus,
    Amendment,
    Candidate,
    FinancialEvent,
    FinancialProfile,
    OutputRow,
    PaymentMethod,
    Request,
    RequestPaymentOption,
)
from observability import get_logger, init_logging, set_request_id, set_stage
from planner.candidates import format_payment_plan, generate_candidates
from planner.ranking import determine_affordability_status, select_best_candidate
from planner.spending import enumerate_viable_spending_combinations, format_spending_changes
from state.amendments import load_message_amendments
from state.fx import FXTable, build_fx_table
from verify.safety import (
    UserContext,
    build_user_context,
    compute_amount_safe_to_pay,
    earliest_date_for_full_payment,
)

logger = get_logger("main")


def process_request(
    req: Request,
    profile: FinancialProfile,
    events: Sequence[FinancialEvent],
    events_by_id: dict[str, FinancialEvent],
    options_by_request: dict[str, list[RequestPaymentOption]],
    fx_table: FXTable,
    amendments: Sequence[Amendment],
) -> tuple[OutputRow, Decimal, date | None]:
    """Process a single request through the full deterministic pipeline."""
    set_request_id(req.request_id)
    req_options = options_by_request.get(req.request_id, [])

    # Build context and baseline forecast curve
    set_stage("forecast")
    context: UserContext = build_user_context(
        user_id=req.user_id,
        request_date=req.request_date,
        opening_balance=profile.current_available_balance,
        minimum_balance_to_keep=profile.minimum_balance_to_keep,
        requested_amount=req.requested_amount,
        events=events,
        amendments=amendments,
        home_currency=profile.home_currency,
        fx_table=fx_table,
        request_id=req.request_id,
    )

    # Compute safety bounds without spending changes
    safe_amt: Decimal = compute_amount_safe_to_pay(context)
    earliest_dt: date | None = earliest_date_for_full_payment(context)

    # Generate viable spending change combinations (max 3, per contract §8)
    set_stage("planning")
    viable_spending = enumerate_viable_spending_combinations(
        req.user_id, req.request_date, profile, events
    )

    # Generate candidate schedules across all methods
    candidates: Sequence[Candidate] = generate_candidates(
        req, profile, req_options, viable_spending, safe_amt, earliest_dt
    )

    # Rank and select best candidate
    chosen: Candidate = select_best_candidate(candidates, req, profile, context)

    # Map candidate to contract output fields
    status: AffordabilityStatus = determine_affordability_status(chosen)
    plan_str: str = format_payment_plan(chosen)
    changes_str: str = format_spending_changes(chosen.spending_changes)
    safe_amt_str: str = format_plan_amount(safe_amt)

    earliest_dt_str: str = ""
    if status != AffordabilityStatus.NOT_AFFORDABLE and earliest_dt is not None:
        earliest_dt_str = earliest_dt.isoformat()

    set_stage("explanation")
    explanation: str = render_decision_explanation(
        chosen,
        context,
        req,
        events_by_id,
        safe_amount=safe_amt,
    )

    row = OutputRow(
        request_id=req.request_id,
        amount_safe_to_pay=safe_amt_str,
        affordability_status=status.value,
        recommended_payment_method=chosen.method.value,
        payment_plan=plan_str,
        earliest_date_for_full_payment=earliest_dt_str,
        spending_changes_needed=changes_str,
        decision_explanation=explanation,
    )

    return row, safe_amt, earliest_dt


def run_pipeline(
    dataset_dir: Path | str = "dataset",
    output_path: Path | str = "output.csv",
    debug: bool = False,
) -> int:
    """Run full evaluation pipeline on requests.csv."""
    init_logging(debug=debug)
    set_stage("init")
    set_request_id("global")
    logger.info("Starting evaluation pipeline")

    data_dir = Path(dataset_dir)
    events = load_financial_events(data_dir / "financial_events.csv")
    events_by_id = {e.event_id: e for e in events}
    profiles = load_financial_profiles(data_dir / "financial_profiles.csv")
    requests = load_requests(data_dir / "requests.csv")
    raw_options = load_request_payment_options(data_dir / "request_payment_options.csv")
    rates = load_exchange_rates(data_dir / "exchange_rates.csv")
    fx_table = build_fx_table(rates)
    amendments = load_message_amendments()

    # Index options by request_id
    options_by_req: dict[str, list[RequestPaymentOption]] = {}
    for opt in raw_options:
        options_by_req.setdefault(opt.request_id, []).append(opt)

    rows: list[OutputRow] = []
    failures: list[tuple[str, str, str]] = []

    status_counts: dict[str, int] = {}
    method_counts: dict[str, int] = {}
    safe_zero_count = 0
    earliest_empty_count = 0

    for req in requests:
        try:
            profile = profiles[req.user_id]
            row, safe_amt, earliest_dt = process_request(
                req=req,
                profile=profile,
                events=events,
                events_by_id=events_by_id,
                options_by_request=options_by_req,
                fx_table=fx_table,
                amendments=amendments,
            )
            rows.append(row)

            # Record stats
            st = str(row.affordability_status)
            mth = str(row.recommended_payment_method)
            status_counts[st] = status_counts.get(st, 0) + 1
            method_counts[mth] = method_counts.get(mth, 0) + 1

            if safe_amt == Decimal("0.00") or safe_amt == Decimal("0"):
                safe_zero_count += 1

            if not row.earliest_date_for_full_payment:
                earliest_empty_count += 1

        except Exception as exc:
            stage = "execution"
            set_stage(stage)
            set_request_id(req.request_id)
            logger.error(f"Failed on {req.request_id}: {exc}")
            failures.append((req.request_id, str(exc), stage))

    set_stage("writer")
    set_request_id("global")
    logger.info(f"Processed {len(rows)}/{len(requests)} successfully with {len(failures)} failures")

    # Write output.csv
    write_output_csv(rows, path=output_path)
    logger.info(f"Wrote {len(rows)} rows to {output_path}")

    # Print summary to stdout
    print("=" * 60)
    print(f"PIPELINE RUN SUMMARY ({len(requests)} requests)")
    print("=" * 60)
    print(f"Completed without error: {len(rows)}/{len(requests)}")
    print(f"Failures: {len(failures)}")
    if failures:
        print("Failure list:")
        for fid, msg, stg in failures:
            print(f"  {fid} at stage [{stg}]: {msg}")

    print("\nAffordability Status Distribution:")
    for k, v in sorted(status_counts.items()):
        print(f"  {k:<25}: {v:>3} ({v/len(requests)*100:>5.1f}%)")

    print("\nRecommended Payment Method Distribution:")
    for k, v in sorted(method_counts.items()):
        print(f"  {k:<25}: {v:>3} ({v/len(requests)*100:>5.1f}%)")

    print(f"\nAmount safe to pay == 0.00: {safe_zero_count} rows")
    print(f"Earliest date empty:       {earliest_empty_count} rows")
    print("=" * 60)

    return 0 if not failures else 1


def main() -> None:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(description="Buy or Wait deterministic financial affordability engine")
    parser.add_argument("--dataset-dir", type=str, default="dataset", help="Path to dataset directory")
    parser.add_argument("--output", type=str, default="output.csv", help="Path to write output.csv")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    sys.exit(run_pipeline(dataset_dir=args.dataset_dir, output_path=args.output, debug=args.debug))


if __name__ == "__main__":
    main()

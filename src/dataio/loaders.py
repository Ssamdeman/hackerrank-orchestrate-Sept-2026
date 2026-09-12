"""Strict, validated loaders for all dataset CSV files.

Owns every read from dataset/. Validates schema and row counts against
docs/data-profile.md. Merges frozen image amounts and asserts zero null survivors.
"""

from __future__ import annotations

import csv
from datetime import date
from decimal import Decimal
import json
from pathlib import Path
from typing import Any

from models import (
    AffordabilityStatus,
    DatasetBundle,
    Direction,
    EventStatus,
    EventType,
    ExchangeRate,
    FinancialEvent,
    FinancialProfile,
    Flexibility,
    ImageMetadata,
    Message,
    OutputRow,
    PaymentMethod,
    Request,
    RequestPaymentOption,
    SampleRequest,
)


_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_DATASET_DIR = _REPO_ROOT / "dataset"
DEFAULT_IMAGE_AMOUNTS_PATH = _REPO_ROOT / "src" / "data" / "image_amounts.json"


def load_image_amounts(path: Path | str | None = None) -> dict[str, Decimal]:
    """Load and parse the frozen 16 image-derived amounts."""
    p = Path(path) if path is not None else DEFAULT_IMAGE_AMOUNTS_PATH
    if not p.is_file():
        raise FileNotFoundError(f"image_amounts.json not found at {p}")

    with open(p, "r", encoding="utf-8") as f:
        raw_data: dict[str, dict[str, Any]] = json.load(f)

    if len(raw_data) != 16:
        raise ValueError(f"Expected exactly 16 image amounts, found {len(raw_data)}")

    amounts: dict[str, Decimal] = {}
    for event_id, item in raw_data.items():
        amt = Decimal(str(item["amount"]))
        if amt <= Decimal(0):
            raise ValueError(f"Non-positive amount for {event_id}: {amt}")
        amounts[event_id] = amt

    return amounts


def load_requests(csv_path: Path | str = DEFAULT_DATASET_DIR / "requests.csv") -> tuple[Request, ...]:
    """Load requests.csv (exactly 250 rows)."""
    p = Path(csv_path)
    if not p.is_file():
        raise FileNotFoundError(f"Missing {p}")

    records: list[Request] = []
    with open(p, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(
                Request(
                    request_id=row["request_id"],
                    user_id=row["user_id"],
                    request_date=date.fromisoformat(row["request_date"]),
                    request_type=row["request_type"],
                    requested_amount=Decimal(row["requested_amount"]),
                    desired_completion_date=date.fromisoformat(row["desired_completion_date"]),
                    allows_partial_payment=row["allows_partial_payment"].strip().lower() in ("true", "1"),
                    request_text=row["request_text"],
                )
            )


    if len(records) != 250:
        raise ValueError(f"Expected 250 requests, found {len(records)}")
    return tuple(records)


def load_financial_profiles(csv_path: Path | str = DEFAULT_DATASET_DIR / "financial_profiles.csv") -> dict[str, FinancialProfile]:
    """Load financial_profiles.csv (exactly 275 rows)."""
    p = Path(csv_path)
    if not p.is_file():
        raise FileNotFoundError(f"Missing {p}")

    profiles: dict[str, FinancialProfile] = {}
    with open(p, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            methods = frozenset(
                PaymentMethod(m.strip()) for m in row["payment_methods_user_will_consider"].split("|") if m.strip()
            )
            priorities = tuple(p.strip() for p in row["financial_priorities"].split("|") if p.strip())
            protect = frozenset(c.strip() for c in row["expense_categories_to_protect"].split("|") if c.strip())

            reduce_val = row.get("expense_categories_user_is_willing_to_reduce") or ""
            reduce_cats = frozenset(c.strip() for c in reduce_val.split("|") if c.strip())

            stop_val = row.get("expense_categories_user_is_willing_to_stop") or ""
            stop_cats = frozenset(c.strip() for c in stop_val.split("|") if c.strip())

            max_inst = row.get("max_installment_months")
            max_inst_val = int(max_inst) if max_inst and max_inst.strip() else None

            prof = FinancialProfile(
                user_id=row["user_id"],
                home_currency=row["home_currency"],
                current_available_balance=Decimal(row["current_available_balance"]),
                minimum_balance_to_keep=Decimal(row["minimum_balance_to_keep"]),
                payment_methods_user_will_consider=methods,
                financial_priorities=priorities,
                expense_categories_to_protect=protect,
                expense_categories_user_is_willing_to_reduce=reduce_cats,
                expense_categories_user_is_willing_to_stop=stop_cats,
                max_installment_months=max_inst_val,
            )
            profiles[prof.user_id] = prof

    if len(profiles) != 275:
        raise ValueError(f"Expected 275 profiles, found {len(profiles)}")
    return profiles


def load_financial_events(
    csv_path: Path | str = DEFAULT_DATASET_DIR / "financial_events.csv",
    image_amounts_path: Path | str | None = None,
) -> tuple[FinancialEvent, ...]:
    """Load financial_events.csv (25,342 rows) and merge 16 frozen image amounts."""
    p = Path(csv_path)
    if not p.is_file():
        raise FileNotFoundError(f"Missing {p}")

    image_amounts = load_image_amounts(image_amounts_path)
    events: list[FinancialEvent] = []

    merged_count = 0
    with open(p, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            event_id = row["event_id"]
            amount_str = row["amount"]

            if not amount_str or amount_str.strip() == "":
                if event_id not in image_amounts:
                    raise ValueError(f"Missing amount for event {event_id} and not found in image_amounts.json")
                amount = image_amounts[event_id]
                merged_count += 1
            else:
                amount = Decimal(amount_str)

            if amount <= Decimal(0):
                raise ValueError(f"Event {event_id} has non-positive amount {amount}")

            settle_str = row.get("settlement_date")
            settlement_date = date.fromisoformat(settle_str) if settle_str and settle_str.strip() else None

            min_amt_str = row.get("minimum_allowed_amount")
            min_allowed = Decimal(min_amt_str) if min_amt_str and min_amt_str.strip() else None

            linked_str = row.get("linked_event_id")
            linked_id = linked_str.strip() if linked_str and linked_str.strip() else None

            events.append(
                FinancialEvent(
                    event_id=event_id,
                    user_id=row["user_id"],
                    event_date=date.fromisoformat(row["event_date"]),
                    settlement_date=settlement_date,
                    amount=amount,
                    currency=row["currency"],
                    direction=Direction(row["direction"]),
                    category=row["category"],
                    description=row["description"],
                    flexibility=Flexibility(row["flexibility"]),
                    minimum_allowed_amount=min_allowed,
                    status=EventStatus(row["status"]),
                    linked_event_id=linked_id,
                    event_type=EventType(row["event_type"]),
                )
            )

    if len(events) != 25342:
        raise ValueError(f"Expected 25,342 events, found {len(events)}")
    if merged_count != 16:
        raise ValueError(f"Expected to merge exactly 16 image amounts, merged {merged_count}")

    return tuple(events)


def load_request_payment_options(csv_path: Path | str = DEFAULT_DATASET_DIR / "request_payment_options.csv") -> tuple[RequestPaymentOption, ...]:
    """Load request_payment_options.csv (exactly 790 rows)."""
    p = Path(csv_path)
    if not p.is_file():
        raise FileNotFoundError(f"Missing {p}")

    options: list[RequestPaymentOption] = []
    with open(p, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            freq_str = row.get("payment_frequency_days")
            freq = int(freq_str) if freq_str and freq_str.strip() else None

            options.append(
                RequestPaymentOption(
                    payment_option_id=row["payment_option_id"],
                    request_id=row["request_id"],
                    payment_method=PaymentMethod(row["payment_method"]),
                    payment_amount=Decimal(row["payment_amount"]),
                    number_of_payments=int(row["number_of_payments"]),
                    first_payment_date=date.fromisoformat(row["first_payment_date"]),
                    payment_frequency_days=freq,
                    financing_fee=Decimal(row["financing_fee"]),
                    total_payable_amount=Decimal(row["total_payable_amount"]),
                )
            )

    if len(options) != 790:
        raise ValueError(f"Expected 790 payment options, found {len(options)}")
    return tuple(options)


def load_exchange_rates(csv_path: Path | str = DEFAULT_DATASET_DIR / "exchange_rates.csv") -> tuple[ExchangeRate, ...]:
    """Load exchange_rates.csv (exactly 134 rows)."""
    p = Path(csv_path)
    if not p.is_file():
        raise FileNotFoundError(f"Missing {p}")

    rates: list[ExchangeRate] = []
    with open(p, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rates.append(
                ExchangeRate(
                    rate_date=date.fromisoformat(row["rate_date"]),
                    from_currency=row["from_currency"],
                    to_currency=row["to_currency"],
                    rate=Decimal(row["rate"]),
                )
            )

    if len(rates) != 134:
        raise ValueError(f"Expected 134 exchange rates, found {len(rates)}")
    return tuple(rates)


def load_messages(csv_path: Path | str = DEFAULT_DATASET_DIR / "messages.csv") -> tuple[Message, ...]:
    """Load messages.csv (exactly 215 rows)."""
    p = Path(csv_path)
    if not p.is_file():
        raise FileNotFoundError(f"Missing {p}")

    messages: list[Message] = []
    with open(p, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            req_str = row.get("request_id")
            req_id = req_str.strip() if req_str and req_str.strip() else None

            rel_str = row.get("related_event_id")
            rel_id = rel_str.strip() if rel_str and rel_str.strip() else None

            messages.append(
                Message(
                    message_id=row["message_id"],
                    user_id=row["user_id"],
                    request_id=req_id,
                    related_event_id=rel_id,
                    sent_at=row["sent_at"],
                    source_type=row["source_type"],
                    message_text=row["message_text"],
                )
            )

    if len(messages) != 215:
        raise ValueError(f"Expected 215 messages, found {len(messages)}")
    return tuple(messages)


def load_images(csv_path: Path | str = DEFAULT_DATASET_DIR / "images.csv") -> tuple[ImageMetadata, ...]:
    """Load images.csv (exactly 16 rows)."""
    p = Path(csv_path)
    if not p.is_file():
        raise FileNotFoundError(f"Missing {p}")

    images: list[ImageMetadata] = []
    with open(p, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            req_str = row.get("request_id")
            req_id = req_str.strip() if req_str and req_str.strip() else None

            images.append(
                ImageMetadata(
                    image_id=row["image_id"],
                    user_id=row["user_id"],
                    request_id=req_id,
                    related_event_id=row["related_event_id"],
                )
            )

    if len(images) != 16:
        raise ValueError(f"Expected 16 images, found {len(images)}")
    return tuple(images)



def load_sample_requests(csv_path: Path | str = DEFAULT_DATASET_DIR / "sample_requests.csv") -> tuple[SampleRequest, ...]:
    """Load sample_requests.csv (exactly 25 rows with ground truth)."""
    p = Path(csv_path)
    if not p.is_file():
        raise FileNotFoundError(f"Missing {p}")

    samples: list[SampleRequest] = []
    with open(p, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            earliest_str = row.get("earliest_date_for_full_payment")
            earliest_date = date.fromisoformat(earliest_str) if earliest_str and earliest_str.strip() else None

            samples.append(
                SampleRequest(
                    request_id=row["request_id"],
                    user_id=row["user_id"],
                    request_date=date.fromisoformat(row["request_date"]),
                    request_type=row["request_type"],
                    requested_amount=Decimal(row["requested_amount"]),
                    desired_completion_date=date.fromisoformat(row["desired_completion_date"]),
                    allows_partial_payment=row["allows_partial_payment"].strip().lower() in ("true", "1"),
                    request_text=row["request_text"],
                    amount_safe_to_pay=Decimal(row["amount_safe_to_pay"]),
                    affordability_status=AffordabilityStatus(row["affordability_status"]),
                    recommended_payment_method=PaymentMethod(row["recommended_payment_method"]),
                    payment_plan=row["payment_plan"],
                    earliest_date_for_full_payment=earliest_date,
                    spending_changes_needed=row["spending_changes_needed"],
                    decision_explanation=row["decision_explanation"],
                )
            )


    if len(samples) != 25:
        raise ValueError(f"Expected 25 sample requests, found {len(samples)}")
    return tuple(samples)


def load_output_template(csv_path: Path | str = DEFAULT_DATASET_DIR / "output.csv") -> tuple[OutputRow, ...]:
    """Load output.csv submission template (exactly 250 rows)."""
    p = Path(csv_path)
    if not p.is_file():
        raise FileNotFoundError(f"Missing {p}")

    rows: list[OutputRow] = []
    with open(p, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(OutputRow(request_id=row["request_id"]))

    if len(rows) != 250:
        raise ValueError(f"Expected 250 rows in output template, found {len(rows)}")
    return tuple(rows)


def load_all(dataset_dir: Path | str = DEFAULT_DATASET_DIR) -> DatasetBundle:
    """Load all 9 dataset CSV files and merge frozen image amounts into a DatasetBundle."""
    d = Path(dataset_dir)
    return DatasetBundle(
        requests=load_requests(d / "requests.csv"),
        financial_profiles=load_financial_profiles(d / "financial_profiles.csv"),
        financial_events=load_financial_events(d / "financial_events.csv"),
        request_payment_options=load_request_payment_options(d / "request_payment_options.csv"),
        exchange_rates=load_exchange_rates(d / "exchange_rates.csv"),
        messages=load_messages(d / "messages.csv"),
        images=load_images(d / "images.csv"),
        sample_requests=load_sample_requests(d / "sample_requests.csv"),
        output_template=load_output_template(d / "output.csv"),
    )

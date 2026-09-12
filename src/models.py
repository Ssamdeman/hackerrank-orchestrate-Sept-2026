"""Shared domain vocabulary, typed records, and data models for Buy or Wait.

All money is Decimal. All records are immutable (frozen dataclasses).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import Enum


# ---------------------------------------------------------------------------
# Closed Value Sets (Enums)
# ---------------------------------------------------------------------------

class Direction(str, Enum):
    """Cash flow direction."""
    DEBIT = "debit"
    CREDIT = "credit"
    NON_CASH = "non_cash"


class EventStatus(str, Enum):
    """Financial event lifecycle status."""
    SETTLED = "settled"
    PENDING = "pending"
    SCHEDULED = "scheduled"
    CANCELLED = "cancelled"
    FAILED = "failed"
    UNREALIZED = "unrealized"


class Flexibility(str, Enum):
    """Event controllability for spending changes."""
    FIXED = "fixed"
    REDUCIBLE = "reducible"
    STOPPABLE = "stoppable"
    REDUCIBLE_OR_STOPPABLE = "reducible_or_stoppable"


class EventType(str, Enum):
    """Categorical event transaction classification."""
    EXPENSE = "expense"
    INCOME = "income"
    SUBSCRIPTION = "subscription"
    DEBT_PAYMENT = "debt_payment"
    REFUND = "refund"
    INVESTMENT_PURCHASE = "investment_purchase"
    INVESTMENT_SALE = "investment_sale"
    INVESTMENT_VALUATION = "investment_valuation"


class AffordabilityStatus(str, Enum):
    """The 4 legal affordability output status values."""
    AFFORDABLE_NOW = "affordable_now"
    AFFORDABLE_WITH_PLAN = "affordable_with_plan"
    AFFORDABLE_LATER = "affordable_later"
    NOT_AFFORDABLE = "not_affordable"


class PaymentMethod(str, Enum):
    """The 5 legal payment method values."""
    FULL_PAYMENT = "full_payment"
    PARTIAL_PAYMENT = "partial_payment"
    INSTALLMENTS = "installments"
    WAIT = "wait"
    NOT_RECOMMENDED = "not_recommended"


# ---------------------------------------------------------------------------
# Dataset Records (Parsed from CSVs)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Request:
    """Evaluation request from requests.csv."""
    request_id: str
    user_id: str
    request_date: date
    request_type: str
    requested_amount: Decimal
    desired_completion_date: date
    allows_partial_payment: bool
    request_text: str



@dataclass(frozen=True)
class FinancialProfile:
    """User preferences and balances from financial_profiles.csv."""
    user_id: str
    home_currency: str
    current_available_balance: Decimal
    minimum_balance_to_keep: Decimal
    payment_methods_user_will_consider: frozenset[PaymentMethod]
    financial_priorities: tuple[str, ...]
    expense_categories_to_protect: frozenset[str]
    expense_categories_user_is_willing_to_reduce: frozenset[str]
    expense_categories_user_is_willing_to_stop: frozenset[str]
    max_installment_months: int | None


@dataclass(frozen=True)
class FinancialEvent:
    """Transaction or commitment record from financial_events.csv."""
    event_id: str
    user_id: str
    event_date: date
    settlement_date: date | None
    amount: Decimal
    currency: str
    direction: Direction
    category: str
    description: str
    flexibility: Flexibility
    minimum_allowed_amount: Decimal | None
    status: EventStatus
    linked_event_id: str | None
    event_type: EventType


@dataclass(frozen=True)
class RequestPaymentOption:
    """Financing option for a request from request_payment_options.csv."""
    payment_option_id: str
    request_id: str
    payment_method: PaymentMethod
    payment_amount: Decimal
    number_of_payments: int
    first_payment_date: date
    payment_frequency_days: int | None
    financing_fee: Decimal
    total_payable_amount: Decimal


@dataclass(frozen=True)
class ExchangeRate:
    """Dated exchange rate from exchange_rates.csv."""
    rate_date: date
    from_currency: str
    to_currency: str
    rate: Decimal


@dataclass(frozen=True)
class Message:
    """Notification or bank message from messages.csv."""
    message_id: str
    user_id: str
    request_id: str | None
    related_event_id: str | None
    sent_at: str
    source_type: str
    message_text: str


@dataclass(frozen=True)
class ImageMetadata:
    """Document mapping from images.csv."""
    image_id: str
    user_id: str
    request_id: str | None
    related_event_id: str



@dataclass(frozen=True)
class SampleRequest:
    """Published ground truth calibration record from sample_requests.csv."""
    request_id: str
    user_id: str
    request_date: date
    request_type: str
    requested_amount: Decimal
    desired_completion_date: date
    allows_partial_payment: bool
    request_text: str
    amount_safe_to_pay: Decimal
    affordability_status: AffordabilityStatus
    recommended_payment_method: PaymentMethod
    payment_plan: str
    earliest_date_for_full_payment: date | None
    spending_changes_needed: str
    decision_explanation: str



@dataclass(frozen=True)
class OutputRow:
    """Row structure for submission output.csv."""
    request_id: str
    amount_safe_to_pay: str | None = None
    affordability_status: str | None = None
    recommended_payment_method: str | None = None
    payment_plan: str | None = None
    earliest_date_for_full_payment: str | None = None
    spending_changes_needed: str | None = None
    decision_explanation: str | None = None


# ---------------------------------------------------------------------------
# Domain & Engine Models
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Flow:
    """Daily balance flow movement."""
    date: date
    amount: Decimal
    direction: Direction
    source_event_id: str | None
    is_projected: bool


@dataclass(frozen=True)
class SeriesKey:
    """Key for recurring event series detection."""
    user_id: str
    direction: Direction
    category: str
    description: str
    currency: str


@dataclass(frozen=True)
class Series:
    """Detected recurring obligation or income stream."""
    key: SeriesKey
    interval_days: int
    latest_amount: Decimal
    occurrences: int
    metadata_event_id: str


@dataclass(frozen=True)
class Payment:
    """Single payment movement inside a candidate plan."""
    date: date
    amount: Decimal


@dataclass(frozen=True)
class SpendingChange:
    """Structured action for an existing recurring expense."""
    event_id: str
    action: str  # 'stop' or 'reduce_to'
    target_amount: Decimal | None


@dataclass(frozen=True)
class Candidate:
    """Candidate payment option under evaluation."""
    method: PaymentMethod
    payments: tuple[Payment, ...]
    spending_changes: tuple[SpendingChange, ...]
    payment_option_id: str | None
    total_paid: Decimal


@dataclass(frozen=True)
class Decision:
    """Final decision recommendation for a request."""
    request_id: str
    amount_safe_to_pay: Decimal
    status: AffordabilityStatus
    method: PaymentMethod
    payment_plan: str
    earliest_date_for_full_payment: date | None
    spending_changes_needed: str
    decision_explanation: str


@dataclass(frozen=True)
class DatasetBundle:
    """Complete in-memory dataset parsed from all 9 CSVs."""
    requests: tuple[Request, ...]
    financial_profiles: dict[str, FinancialProfile]
    financial_events: tuple[FinancialEvent, ...]
    request_payment_options: tuple[RequestPaymentOption, ...]
    exchange_rates: tuple[ExchangeRate, ...]
    messages: tuple[Message, ...]
    images: tuple[ImageMetadata, ...]
    sample_requests: tuple[SampleRequest, ...]
    output_template: tuple[OutputRow, ...]

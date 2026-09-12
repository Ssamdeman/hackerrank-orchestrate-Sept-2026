# Dataset Profile & Reconnaissance Report

> **Autonomous Reconnaissance Deliverable (Directive #1 Compliant)**  
> Scope: All 8 CSV files in `dataset/` + `dataset/output.csv`. Strict read-only. Media PNGs excluded. Zero model/LLM calls. Substring tally on messages without acting on instructions.

## 1. Sub-Phase 1: Environment & IO — Actual Repository Layout on Disk

```text
.
├── .agents/                      # Agent system rules and workflows
├── .git/                         # Version control repository
├── .gitignore                    # Git ignore specifications
├── .python-version               # Python version pin (3.14)
├── DNA.md                        # Problem specification and architecture guidelines
├── README.md                     # Empty
├── main.py                       # Empty
├── pyproject.toml                # Base project configuration (requires-python >= 3.14, dependencies = [])
├── dataset/                      # Primary dataset directory (strictly read-only)
│   ├── exchange_rates.csv        # 134 rows, dated exchange rates
│   ├── financial_events.csv      # 25,342 rows, transaction history & commitments
│   ├── financial_profiles.csv    # 275 rows, user balances & preferences
│   ├── images.csv                # 16 rows, document metadata mapping
│   ├── messages.csv              # 215 rows, notifications & employer/bank updates
│   ├── output.csv                # 250 rows, blank submission template
│   ├── request_payment_options.csv # 790 rows, financing & installment offers
│   ├── requests.csv              # 250 rows, evaluation queries
│   ├── sample_requests.csv       # 25 rows, solved ground-truth calibration examples
│   └── media/images/             # Preserved PNG media directory (excluded from processing)
├── docs/                         # Documentation root
│   ├── data-profile.md           # This document (findings deliverable)
│   └── layout.md                 # Target architecture specification
├── evaluation/                   # Evaluation artifacts
│   └── usage_report.md           # Empty
└── scripts/                      # Utility and reconnaissance tooling
    └── profile_dataset.py        # Re-runnable profiling script
```

### Target Layout & Environment Deviations
- **`src/` directory**: Defined in `docs/layout.md` as the target solution package; currently **not present** on disk.
- **`scripts/` directory**: Created during this reconnaissance task to house `profile_dataset.py`.
- **`pyproject.toml` dependencies**: Currently empty (`dependencies = []`). The local virtual environment provides Python 3.14.7, `uv` 0.9.21, and `pandas` 3.0.5.

## 2. Sub-Phase 2: Base Profiling — Dataset Overview Table

| File | Rows | Columns | Null Columns (Count) | Description |
|---|---|---|---|---|
| `requests.csv` | 250 | 8 | None | Primary data table |
| `output.csv` | 250 | 8 | `amount_safe_to_pay` (250), `affordability_status` (250), `recommended_payment_method` (250), `payment_plan` (250), `earliest_date_for_full_payment` (250), `spending_changes_needed` (250), `decision_explanation` (250) | Primary data table |
| `sample_requests.csv` | 25 | 15 | `earliest_date_for_full_payment` (7) | Primary data table |
| `financial_profiles.csv` | 275 | 10 | `expense_categories_user_is_willing_to_reduce` (39), `expense_categories_user_is_willing_to_stop` (62), `max_installment_months` (119) | Primary data table |
| `financial_events.csv` | 25,342 | 14 | `amount` (16), `settlement_date` (10), `linked_event_id` (25284), `minimum_allowed_amount` (22435) | Primary data table |
| `request_payment_options.csv` | 790 | 9 | `payment_frequency_days` (275) | Primary data table |
| `exchange_rates.csv` | 134 | 4 | None | Primary data table |
| `messages.csv` | 215 | 7 | `request_id` (87), `related_event_id` (176) | Primary data table |
| `images.csv` | 16 | 4 | None | Primary data table |

## 3. Sub-Phase 3: Formats, Chains & Calibration Specifics

### 3.1 `financial_profiles.csv`: Format & Cardinality
- **User Cardinality**: Exactly **275 rows** and **275 distinct `user_id`s**. Exactly **one row per user**.
- **Field Format**: Fields use pipe-delimited tokens (`|`) for multi-value preferences and lists.
- **Raw Samples (5 verbatim values each)**:

  **`payment_methods_user_will_consider`**:
  - `full_payment`
  - `partial_payment|installments`
  - `full_payment|partial_payment|installments`
  - `full_payment`
  - `full_payment|partial_payment|installments`

  **`financial_priorities`**:
  - `education|debt_repayment`
  - `education|family_support`
  - `retirement_investment|emergency_savings`
  - `education|emergency_savings`
  - `healthcare|family_support`

  **`expense_categories_to_protect`** (spending preferences):
  - `rent|education|groceries|debt_repayment`
  - `housing|utilities|education`
  - `rent|utilities|groceries`
  - `rent|groceries|transport`
  - `rent|healthcare|family_support|groceries`

  **`expense_categories_user_is_willing_to_reduce`**:
  - `dining`
  - `entertainment`
  - `streaming|shopping`
  - `entertainment`
  - `shopping`

  **`expense_categories_user_is_willing_to_stop`**:
  - `delivery_membership`
  - `cloud_storage`
  - `streaming|cloud_storage`
  - `music_subscription`
  - `cloud_storage`

### 3.2 `financial_events.csv`: Structure, Recurrence, Chains & Blank Amounts
- **Recurring vs One-Time**: There is **no explicit `is_recurring` boolean or interval column** in `financial_events.csv`. Recurrence is implicit in `event_type` (`subscription`, `income`, `debt_payment` vs `expense`), event descriptions (e.g. *Music service subscription*, *Delivery service plan*), and repeated monthly timestamps.
- **Flexibility Column**: Explicitly indicated by `flexibility` with 4 categorical values: `fixed` (21,138), `reducible` (2,682), `stoppable` (1,297), and `reducible_or_stoppable` (225).
- **Status Column**: Explicitly indicated by `status` with 6 categorical values: `settled` (25,148), `pending` (71), `scheduled` (70), `cancelled` (22), `failed` (21), and `unrealized` (10). Note: `refund` is recorded as an `event_type` (22 rows), not a status value.
- **Recurrence Interval**: Not expressed in `financial_events.csv`. In `request_payment_options.csv`, recurrence is expressed in days via `payment_frequency_days`.
- **Direction & Sign**: The `amount` column is **strictly positive** (min: `2.0`, max: `48,830,000.0`, zero negative values). Flow direction is stored in the dedicated `direction` column with values `debit` (23,609), `credit` (1,723), and `non_cash` (10).
- **Blank Amount Rows**: Exactly **16 rows** have a blank `amount`. All 16 events and their identifiers:

  | Event ID | User ID | Event Type | Description | Currency |
  |---|---|---|---|---|
  | `event_253` | `user_03` | `income` | August 2019 net salary | `IDR` |
  | `event_1442` | `user_16` | `expense` | Outstanding rent balance | `INR` |
  | `event_1545` | `user_17` | `expense` | Bulk groceries and pantry purchase | `INR` |
  | `event_1700` | `user_19` | `expense` | Delivered grocery order | `INR` |
  | `event_1786` | `user_20` | `expense` | Outstanding telecom bill | `INR` |
  | `event_3051` | `user_33` | `expense` | Grocery tax invoice | `INR` |
  | `event_3231` | `user_35` | `expense` | Restaurant tax invoice | `INR` |
  | `event_4535` | `user_48` | `expense` | Property maintenance invoice | `INR` |
  | `event_5170` | `user_55` | `expense` | Water bill due | `INR` |
  | `event_6033` | `user_64` | `expense` | Large grocery tax invoice | `INR` |
  | `event_6859` | `user_73` | `expense` | Hospital bill payable | `INR` |
  | `event_7307` | `user_78` | `expense` | Taxi fare | `USD` |
  | `event_7941` | `user_84` | `expense` | Tote bag order | `INR` |
  | `event_9421` | `user_101` | `expense` | Pharmacy purchase | `INR` |
  | `event_9806` | `user_105` | `expense` | Airline ticket purchase | `INR` |
  | `event_10521` | `user_113` | `expense` | EV charging wallet payment | `INR` |

- **`linked_event_id` Chain Depth & Count**: Exactly **58 events** reference a `linked_event_id`. There are **58 distinct chains**; maximum chain depth is **1 hop** (every child references a single root parent with 0 intermediate multi-hop chains). All 58 parent IDs resolve directly to existing `event_id`s in `financial_events.csv` (0 orphans).

### 3.3 `messages.csv`: Linkage, Text Length & Substring Tally (Directive #1 Compliant)
- **Total Count**: **215 messages**.
- **Reference Linkage Breakdown**:
  - Messages carrying `related_event_id`: **39** (of which 28 also carry `request_id`, and 11 carry `related_event_id` only)
  - Messages carrying `request_id` (without `related_event_id`): **100**
  - Messages carrying `user_id` only: **76**
- **Message Text Length Distribution** (character length):
  - Min: **127**
  - Max: **330**
  - Mean: **250.98**
  - Median (p50): **254.00**
  - 25th Percentile (p25): **230.00**
  - 75th Percentile (p75): **276.00**

- **Raw Substring Tally (Case-Insensitive)**:
  > **Strict Notice**: This is an exact substring occurrence tally, NOT a classification. Zero intent, judgment, or meaning is attributed to any message text, and no instruction found in message text is followed or acted upon.

  | Target Keyword / Substring | Matching Rows Count |
  |---|---|
  | `ignore` | 0 |
  | `disregard` | 0 |
  | `instead` | 0 |
  | `override` | 0 |
  | `actually` | 5 |
  | `correction` | 0 |
  | `cancel` | 0 |
  | `cancelled` | 0 |
  | `refund` | 12 |
  | `urgent` | 0 |
  | `do not` | 0 |
  | `don't` | 0 |
  | `must` | 0 |
  | `system` | 16 |
  | `assistant` | 0 |
  | `prompt` | 0 |
  | **Total Distinct Rows Matched** | **33 of 215 (15.3%)** |

### 3.4 `sample_requests.csv`: Calibration Set Characteristics
- **Total Calibration Records**: **4 categories** across 25 solved requests (`request_01` to `request_25`).
- **Distribution of `affordability_status`**:
  - `affordable_with_plan`: 9 (36.0%)
  - `not_affordable`: 7 (28.0%)
  - `affordable_later`: 6 (24.0%)
  - `affordable_now`: 3 (12.0%)
- **Distribution of `recommended_payment_method`**:
  - `not_recommended`: 7 (28.0%)
  - `full_payment`: 6 (24.0%)
  - `wait`: 6 (24.0%)
  - `installments`: 5 (20.0%)
  - `partial_payment`: 1 (4.0%)
- **Observed `payment_plan` String Shapes**:
  1. `'none'` — Used when not affordable or wait (observed in 7 cases).
  2. Single payment: `'YYYY-MM-DD:amount'` — e.g. `'2024-03-03:25256'` or `'2026-01-03:620.40'` (observed in 8 cases).
  3. Installment sequence: `'YYYY-MM-DD:amount|YYYY-MM-DD:amount|...'` — pipe-separated schedule with uniform installment amounts (observed in 5 cases).
  4. Multi-payment partial sequence: `'YYYY-MM-DD:amount|YYYY-MM-DD:amount'` — pipe-separated schedule with differing amounts (observed in 1 case: `'2024-09-04:28820|2024-09-15:10840'`).
- **`earliest_date_for_full_payment` Presence**: Populated in **18 cases** (72.0%); Empty/null in **7 cases** (28.0%, strictly when `affordability_status == 'not_affordable'`).
- **`decision_explanation` Character Length**: Min: **85**, Max: **158**, Mean: **113.3**, Median: **113.0** characters.

### 3.5 `output.csv`: Verbatim Header & Structure
- **Verbatim Header Line**:
  ```csv
  request_id,amount_safe_to_pay,affordability_status,recommended_payment_method,payment_plan,earliest_date_for_full_payment,spending_changes_needed,decision_explanation
  ```
- **Row Population**: Contains **250 rows** with pre-populated `request_id` (`request_26` through `request_275`). All 7 prediction columns are completely unpopulated (250 nulls each).

## 4. Sub-Phase 4: Relational Cross-Checks & Integrity Audits

### 4.1 Exchange-Rate Coverage (Joining `financial_events.csv` to `financial_profiles.csv` on `user_id`)
- **Join Specification**: `financial_events.csv` is joined to `financial_profiles.csv` on `user_id` to resolve each user's `home_currency`.
- **Non-Home-Currency Events Identified**: Exactly **140 events** have `currency != home_currency`.
- **Direct Dated Rate Matches**: Exactly **140 events** (100.0%) have an exact dated rate in `exchange_rates.csv` matching `from_currency = event_currency`, `to_currency = home_currency`, and `rate_date = event_date`.
- **Rate Gaps**: Exactly **0 gaps**. Every foreign transaction resolves directly.
- **Available Pairs (5)**: `EUR` → `ZAR`, `USD` → `EUR`, `USD` → `IDR`, `USD` → `INR`, `EUR` → `USD`
- **Rate Date Range**: `2023-10-15` to `2026-11-15` (39 dates, 134 rows).

### 4.2 Payment-Option Reconciliation (Joining `request_payment_options.csv` to `requests.csv` on `request_id`)
- **Join Specification**: `request_payment_options.csv` is joined to `requests.csv` (and `sample_requests.csv`) on `request_id` to resolve `requested_amount`.
- **Options-per-Request Distribution** (275 total requests):
  - **2 options**: 65 requests (130 option records)
  - **3 options**: 180 requests (540 option records)
  - **4 options**: 30 requests (120 option records)
  - Total Option Records: **790**
- **Field Names Defined**: Start date: `first_payment_date`, Interval: `payment_frequency_days`, Count: `number_of_payments`, Fee: `financing_fee`, Total: `total_payable_amount`.
- **Fee Reconciliation** (`total_payable_amount == requested_amount + financing_fee`): Exactly **0 mismatches** across all 790 options (100.0% exact match).
- **Installment Reconciliation** (`total_payable_amount == payment_amount * number_of_payments`): Exactly **0 mismatches** across all 790 options (100.0% exact match).

### 4.3 Bidirectional Orphan Audits & Image Mapping

| Entity Relationship | Source Table | Target Table | Orphan Count | Verification Status |
|---|---|---|---|---|
| `user_id` | `requests.csv` | `financial_profiles.csv` | 0 | Clean (100% matched) |
| `user_id` | `sample_requests.csv` | `financial_profiles.csv` | 0 | Clean (100% matched) |
| `user_id` | `financial_events.csv` | `financial_profiles.csv` | 0 | Clean (100% matched) |
| `user_id` | `messages.csv` | `financial_profiles.csv` | 0 | Clean (100% matched) |
| `user_id` | `images.csv` | `financial_profiles.csv` | 0 | Clean (100% matched) |
| `user_id` (reverse) | `financial_profiles.csv` | All Requests (`req` + `sreq`) | 0 | Clean (Every user has exactly 1 request) |
| `request_id` | `output.csv` | `requests.csv` | 0 | Clean (Exact 1-to-1 match for requests 26–275) |
| `request_id` | `request_payment_options.csv` | All Requests | 0 | Clean (100% matched) |
| `request_id` (coverage) | All Requests | `request_payment_options.csv` | 0 | Clean (0 requests with zero payment options) |
| `request_id` | `messages.csv` | All Requests | 0 | Clean (100% matched) |
| `request_id` | `images.csv` | All Requests | 0 | Clean (100% matched) |
| `related_event_id` | `messages.csv` | `financial_events.csv` | 0 | Clean (100% matched) |
| `related_event_id` | `images.csv` | `financial_events.csv` | 0 | Clean (100% matched) |
| `linked_event_id` | `financial_events.csv` | `financial_events.csv` | 0 | Clean (100% self-referential integrity) |

- **Image Mapping to Blank Events**: Exactly **16 of 16 blank-amount financial events** (100.0%) link to an image in `images.csv` (and 100.0% of images map to a blank-amount event).

## 5. Exhaustive Per-File Column Profiles

### 5.1 `requests.csv`
- **Dimensions**: 250 rows × 8 columns
- **Raw Header**: `request_id,user_id,request_date,request_type,requested_amount,desired_completion_date,allows_partial_payment,request_text`

| Column Order | Column Name | Inferred Dtype | Null Count | Unique Count | Value Characteristics & Bounds |
|---|---|---|---|---|---|
| 1 | `request_id` | `str` | 0 | 250 | High-cardinality string/identifier (250 unique) |
| 2 | `user_id` | `str` | 0 | 250 | High-cardinality string/identifier (250 unique) |
| 3 | `request_date` | `str` | 0 | 61 | Date Range: [2023-01-20, 2026-09-04]<br>Format: Consistent YYYY-MM-DD |
| 4 | `request_type` | `str` | 0 | 9 | Distribution: `family_transfer`: 28, `purchase`: 28, `investment`: 28, `debt_repayment`: 28, `travel`: 28, `housing`: 28, `education`: 28, `emergency_expense`: 27, `other`: 27 |
| 5 | `requested_amount` | `float64` | 0 | 248 | Range: [199.89, 83,923,000.0]<br>Has Negatives: False |
| 6 | `desired_completion_date` | `str` | 0 | 170 | Date Range: [2023-02-13, 2026-10-19]<br>Format: Consistent YYYY-MM-DD |
| 7 | `allows_partial_payment` | `bool` | 0 | 2 | Distribution: `false`: 170, `true`: 80 |
| 8 | `request_text` | `str` | 0 | 250 | High-cardinality string/identifier (250 unique) |

### 5.2 `output.csv`
- **Dimensions**: 250 rows × 8 columns
- **Raw Header**: `request_id,amount_safe_to_pay,affordability_status,recommended_payment_method,payment_plan,earliest_date_for_full_payment,spending_changes_needed,decision_explanation`

| Column Order | Column Name | Inferred Dtype | Null Count | Unique Count | Value Characteristics & Bounds |
|---|---|---|---|---|---|
| 1 | `request_id` | `str` | 0 | 250 | High-cardinality string/identifier (250 unique) |
| 2 | `amount_safe_to_pay` | `float64` | 250 | 0 | Range: [nan, nan]<br>Has Negatives: False |
| 3 | `affordability_status` | `float64` | 250 | 0 | Range: [nan, nan]<br>Has Negatives: False |
| 4 | `recommended_payment_method` | `float64` | 250 | 0 | Range: [nan, nan]<br>Has Negatives: False |
| 5 | `payment_plan` | `float64` | 250 | 0 | Range: [nan, nan]<br>Has Negatives: False |
| 6 | `earliest_date_for_full_payment` | `float64` | 250 | 0 | Date Range: [None, None]<br>Format: None (All Null) |
| 7 | `spending_changes_needed` | `float64` | 250 | 0 | Range: [nan, nan]<br>Has Negatives: False |
| 8 | `decision_explanation` | `float64` | 250 | 0 | Range: [nan, nan]<br>Has Negatives: False |

### 5.3 `sample_requests.csv`
- **Dimensions**: 25 rows × 15 columns
- **Raw Header**: `request_id,user_id,request_date,request_type,requested_amount,desired_completion_date,allows_partial_payment,request_text,amount_safe_to_pay,affordability_status,recommended_payment_method,payment_plan,earliest_date_for_full_payment,spending_changes_needed,decision_explanation`

| Column Order | Column Name | Inferred Dtype | Null Count | Unique Count | Value Characteristics & Bounds |
|---|---|---|---|---|---|
| 1 | `request_id` | `str` | 0 | 25 | High-cardinality string/identifier (25 unique) |
| 2 | `user_id` | `str` | 0 | 25 | High-cardinality string/identifier (25 unique) |
| 3 | `request_date` | `str` | 0 | 25 | Date Range: [2019-09-03, 2026-07-07]<br>Format: Consistent YYYY-MM-DD |
| 4 | `request_type` | `str` | 0 | 9 | Distribution: `purchase`: 3, `travel`: 3, `education`: 3, `family_transfer`: 3, `debt_repayment`: 3, `investment`: 3, `housing`: 3, `emergency_expense`: 2, `other`: 2 |
| 5 | `requested_amount` | `float64` | 0 | 25 | Range: [166.61, 60,496,000.0]<br>Has Negatives: False |
| 6 | `desired_completion_date` | `str` | 0 | 24 | Date Range: [2019-11-15, 2026-09-15]<br>Format: Consistent YYYY-MM-DD |
| 7 | `allows_partial_payment` | `bool` | 0 | 2 | Distribution: `false`: 13, `true`: 12 |
| 8 | `request_text` | `str` | 0 | 25 | Distribution: `Would paying for the laptop today leave enough for my regular expenses? The laptop I'm looking at is ZAR 25,256.`: 1, `The current quote for the trip is IDR 46,018,000. I need to complete it by 10 October 2025. Can I afford the full trip without putting upcoming bills at risk?`: 1, `Should I pay for the course now, use installments, or wait? I need to decide by 15 November 2019. The course I want to take is IDR 5,491,000.`: 1, `The amount I want to send is IDR 12,693,000. Would sending the money now leave enough for my upcoming expenses?`: 1, `Can I clear this additional amount without putting upcoming bills at risk? The extra repayment I'm considering is ZAR 15,488.`: 1, `I want to put EUR 620.40 into an investment. I need to complete it by 14 January 2026. Is it safer to invest now, invest a smaller amount, or wait?`: 1, `How much of the rental deposit can I safely pay today? I need to decide by 14 November 2024. The rental deposit is INR 197,400.`: 1, `The repair I need is priced at EUR 996.60. Can I cover the full repair now and still manage my essential expenses?`: 1, `Is the full membership fee affordable today, or should I wait? The annual membership costs EUR 166.61.`: 1, `The price of the laptop is INR 266,700. I need to complete it by 10 February 2025. How much of the laptop price can I safely cover today?`: 1, `Does paying for the trip now leave enough for the rest of the month? I need to decide by 12 June 2025. I'm planning a family trip that costs IDR 13,110,000.`: 1, `The professional course costs ZAR 65,164. Can I pay for the course before enrolment closes?`: 1, `Can I complete this family transfer and still keep my minimum balance? I want to send EUR 941.60 to my family.`: 1, `I'm planning an extra loan payment of EUR 5,414.20. I need to complete it by 4 October 2025. Would paying this much toward the loan leave enough for the rest of the month?`: 1, `How much can I invest now without affecting essential payments? I need to decide by 1 February 2026. I have an opportunity to invest EUR 3,685.`: 1, `The landlord has asked for a deposit of INR 122,500. Can I pay the rental deposit by the requested date?`: 1, `What is the most I can put toward this repair right now? The latest estimate for the repair is INR 274,600.`: 1, `The annual plan comes to EUR 3,246.10. I need to complete it by 15 September 2026. Can I take the membership and still keep my minimum balance intact?`: 1, `Can I buy the laptop now without making next month's bills tight? I need to decide by 4 October 2024. I've been quoted INR 39,660 for the laptop.`: 1, `I can book the family trip for INR 303,700. Would it be safer to book the trip now or wait until more money comes in?`: 1, `Is it safe to cover the full course fee by the deadline? Enrolment for the course comes to USD 1,574.40.`: 1, `The transfer I have in mind is EUR 731.50. I need to complete it by 10 February 2025. Can I make the full transfer without falling short on my own bills?`: 1, `How much extra can I put toward the loan today? I need to decide by 15 July 2025. The additional loan payment would be ZAR 38,016.`: 1, `I'm considering setting aside INR 109,600 for an investment. Would investing this amount leave my upcoming bills covered?`: 1, `Is the deposit affordable now, or do I need more time? I need IDR 60,496,000 for the rental deposit.`: 1 |
| 9 | `amount_safe_to_pay` | `float64` | 0 | 25 | Range: [83.05, 17,229,139.2]<br>Has Negatives: False |
| 10 | `affordability_status` | `str` | 0 | 4 | Distribution: `affordable_with_plan`: 9, `not_affordable`: 7, `affordable_later`: 6, `affordable_now`: 3 |
| 11 | `recommended_payment_method` | `str` | 0 | 5 | Distribution: `not_recommended`: 7, `full_payment`: 6, `wait`: 6, `installments`: 5, `partial_payment`: 1 |
| 12 | `payment_plan` | `str` | 0 | 19 | Distribution: `none`: 7, `2024-03-03:25256`: 1, `2025-08-08:15952906.67|2025-09-07:15952906.67|2025-10-07:15952906.67`: 1, `2019-11-15:5491000`: 1, `2024-06-15:12693000`: 1, `2026-01-03:620.40`: 1, `2024-09-12:68432|2024-10-10:68432|2024-11-07:68432`: 1, `2025-04-15:996.60`: 1, `2026-07-04:166.61`: 1, `2025-05-03:13110000`: 1, `2026-04-19:22590.19|2026-05-20:22590.19|2026-06-20:22590.19`: 1, `2024-05-15:941.60`: 1, `2023-08-12:122500`: 1, `2026-03-01:95194.67|2026-03-31:95194.67|2026-04-30:95194.67`: 1, `2026-09-15:3246.10`: 1, `2024-09-04:28820|2024-09-15:10840`: 1, `2026-04-03:1574.40`: 1, `2024-12-08:253.59|2025-01-05:253.59|2025-02-02:253.59`: 1, `2025-07-15:38016`: 1 |
| 13 | `earliest_date_for_full_payment` | `str` | 7 | 17 | Date Range: [2019-11-15, 2026-09-15]<br>Format: Consistent YYYY-MM-DD |
| 14 | `spending_changes_needed` | `str` | 0 | 4 | Distribution: `none`: 22, `stop:event_476`: 1, `reduce_to:event_989:665950`: 1, `stop:event_1815|reduce_to:event_1816:23.50`: 1 |
| 15 | `decision_explanation` | `str` | 0 | 25 | Distribution: `Pay ZAR 25,256 today. This leaves at least ZAR 18,000 available over the next 90 days.`: 1, `Use 3 installments of IDR 15,952,906.67, starting 8 August 2025. This leaves at least IDR 29,158,400 available.`: 1, `Pay IDR 5,491,000 in full on 15 November 2019. Paying earlier would take the balance below the IDR 2,668,700 minimum.`: 1, `Wait until 15 June 2024, then pay IDR 12,693,000 in full. Paying sooner would put the IDR 30,686,600 minimum at risk.`: 1, `Do not make this payment by 12 January 2026. None of the available options keeps the ZAR 13,100 minimum protected.`: 1, `Stop the family streaming plan, then pay EUR 620.40 today. This leaves at least EUR 800 available.`: 1, `Use 3 installments of INR 68,432, starting 12 September 2024. This leaves at least INR 93,000 available.`: 1, `Pay EUR 996.60 in full on 15 April 2025. Paying earlier would take the balance below the EUR 800 minimum.`: 1, `Pay EUR 166.61 today. This keeps the EUR 600 minimum available over the next 90 days.`: 1, `Do not make this payment by 10 February 2025. None of the available options keeps the INR 225,400 minimum protected.`: 1, `Reduce the weekend food delivery to IDR 665,950, then pay IDR 13,110,000 today. This leaves at least IDR 34,140,600 available.`: 1, `Use 3 installments of ZAR 22,590.19, starting 19 April 2026. This leaves at least ZAR 43,200 available.`: 1, `Pay EUR 941.60 in full on 15 May 2024. Paying earlier would take the balance below the EUR 1,300 minimum.`: 1, `Do not proceed with the EUR 5,414.20 request. Although EUR 597.74 is available today, the full amount cannot be completed safely within 90 days.`: 1, `Do not make this payment by 1 February 2026. None of the available options keeps the EUR 1,200 minimum protected.`: 1, `Pay INR 122,500 today. This leaves at least INR 122,400 available over the next 90 days.`: 1, `Use 3 installments of INR 95,194.67, starting 1 March 2026. This leaves at least INR 166,100 available.`: 1, `Pay EUR 3,246.10 in full on 15 September 2026. Paying earlier would take the balance below the EUR 1,400 minimum.`: 1, `Pay INR 28,820 today and the remaining INR 10,840 on 15 September 2024. This completes the full request and keeps the INR 92,800 minimum protected.`: 1, `Do not make this payment by 22 February 2026. None of the available options keeps the INR 64,500 minimum protected.`: 1, `Stop the online backup subscription and reduce the streaming subscription to USD 23.50, then pay USD 1,574.40 today. This leaves at least USD 1,800 available.`: 1, `Use 3 installments of EUR 253.59, starting 8 December 2024. This leaves at least EUR 500 available.`: 1, `Pay ZAR 38,016 in full on 15 July 2025. Paying earlier would take the balance below the ZAR 27,000 minimum.`: 1, `Do not proceed with the INR 109,600 request. Although INR 13,420 is available today, the full amount cannot be completed safely within 90 days.`: 1, `Do not make this payment by 17 April 2024. None of the available options keeps the IDR 23,379,100 minimum protected.`: 1 |

### 5.4 `financial_profiles.csv`
- **Dimensions**: 275 rows × 10 columns
- **Raw Header**: `user_id,home_currency,current_available_balance,minimum_balance_to_keep,financial_priorities,expense_categories_to_protect,expense_categories_user_is_willing_to_reduce,expense_categories_user_is_willing_to_stop,payment_methods_user_will_consider,max_installment_months`

| Column Order | Column Name | Inferred Dtype | Null Count | Unique Count | Value Characteristics & Bounds |
|---|---|---|---|---|---|
| 1 | `user_id` | `str` | 0 | 275 | High-cardinality string/identifier (275 unique) |
| 2 | `home_currency` | `str` | 0 | 5 | Distribution: `INR`: 67, `EUR`: 62, `IDR`: 55, `ZAR`: 51, `USD`: 40 |
| 3 | `current_available_balance` | `float64` | 0 | 275 | Range: [683.69, 136,691,818.94]<br>Has Negatives: False |
| 4 | `minimum_balance_to_keep` | `int64` | 0 | 192 | Range: [400, 41,430,800]<br>Has Negatives: False |
| 5 | `financial_priorities` | `str` | 0 | 9 | Distribution: `emergency_savings|travel`: 46, `retirement_investment|emergency_savings`: 42, `education|debt_repayment`: 36, `education|emergency_savings`: 34, `emergency_savings|housing`: 29, `healthcare|family_support`: 25, `education|family_support`: 24, `debt_repayment|emergency_savings`: 20, `healthcare|retirement_investment`: 19 |
| 6 | `expense_categories_to_protect` | `str` | 0 | 8 | Distribution: `rent|groceries|transport`: 63, `rent|insurance|transport`: 46, `rent|utilities|groceries`: 42, `rent|education|groceries|debt_repayment`: 36, `rent|healthcare|family_support|groceries`: 25, `housing|utilities|education`: 24, `rent|utilities|debt_repayment`: 20, `housing|healthcare|utilities`: 19 |
| 7 | `expense_categories_user_is_willing_to_reduce` | `str` | 39 | 18 | Distribution: `dining`: 80, `nan`: 39, `shopping`: 35, `dining|streaming`: 22, `dining|entertainment`: 20, `streaming`: 17, `dining|streaming|shopping`: 12, `dining|shopping`: 10, `streaming|shopping`: 8, `gym`: 6, `entertainment`: 5, `streaming|entertainment`: 5, `dining|gym|entertainment`: 4, `shopping|entertainment`: 4, `dining|gym`: 2, `gym|entertainment`: 2, `dining|shopping|entertainment`: 2, `streaming|shopping|entertainment`: 1, `dining|streaming|entertainment`: 1 |
| 8 | `expense_categories_user_is_willing_to_stop` | `str` | 62 | 10 | Distribution: `nan`: 62, `cloud_storage`: 57, `streaming|cloud_storage`: 52, `streaming`: 32, `music_subscription`: 26, `music_subscription|delivery_membership`: 24, `delivery_membership`: 10, `gym|music_subscription`: 4, `gym|music_subscription|delivery_membership`: 4, `gym|delivery_membership`: 3, `gym`: 1 |
| 9 | `payment_methods_user_will_consider` | `str` | 0 | 7 | Distribution: `full_payment`: 60, `partial_payment|installments`: 52, `installments`: 41, `full_payment|partial_payment`: 40, `full_payment|installments`: 35, `full_payment|partial_payment|installments`: 28, `partial_payment`: 19 |
| 10 | `max_installment_months` | `float64` | 119 | 11 | Range: [2, 12]<br>Has Negatives: False |

### 5.5 `financial_events.csv`
- **Dimensions**: 25,342 rows × 14 columns
- **Raw Header**: `event_id,user_id,event_type,description,category,direction,amount,currency,event_date,settlement_date,status,linked_event_id,flexibility,minimum_allowed_amount`

| Column Order | Column Name | Inferred Dtype | Null Count | Unique Count | Value Characteristics & Bounds |
|---|---|---|---|---|---|
| 1 | `event_id` | `str` | 0 | 25342 | High-cardinality string/identifier (25342 unique) |
| 2 | `user_id` | `str` | 0 | 275 | High-cardinality string/identifier (275 unique) |
| 3 | `event_type` | `str` | 0 | 8 | Distribution: `expense`: 20525, `subscription`: 2488, `income`: 1696, `debt_payment`: 567, `investment_purchase`: 29, `refund`: 22, `investment_valuation`: 10, `investment_sale`: 5 |
| 4 | `description` | `str` | 0 | 164 | High-cardinality string/identifier (164 unique) |
| 5 | `category` | `str` | 0 | 22 | Distribution: `groceries`: 5812, `transport`: 5626, `dining`: 3479, `salary`: 1690, `utilities`: 1452, `rent`: 1355, `cloud_storage`: 833, `shopping`: 813, `streaming`: 683, `debt_repayment`: 553, `entertainment`: 521, `insurance`: 456, `music_subscription`: 451, `healthcare`: 356, `delivery_membership`: 351, `education`: 306, `housing`: 246, `gym`: 170, `family_support`: 125, `investment`: 44, `work_expense`: 14, `windfall`: 6 |
| 6 | `direction` | `str` | 0 | 3 | Distribution: `debit`: 23609, `credit`: 1723, `non_cash`: 10 |
| 7 | `amount` | `float64` | 16 | 17785 | Range: [2.0, 48,830,000.0]<br>Has Negatives: False |
| 8 | `currency` | `str` | 0 | 5 | Distribution: `INR`: 6457, `EUR`: 5585, `IDR`: 4992, `ZAR`: 4489, `USD`: 3819 |
| 9 | `event_date` | `str` | 0 | 1308 | Date Range: [2019-03-09, 2026-09-03]<br>Format: Consistent YYYY-MM-DD |
| 10 | `settlement_date` | `str` | 10 | 1310 | Date Range: [2019-03-09, 2026-09-03]<br>Format: Consistent YYYY-MM-DD |
| 11 | `status` | `str` | 0 | 6 | Distribution: `settled`: 25148, `pending`: 71, `scheduled`: 70, `cancelled`: 22, `failed`: 21, `unrealized`: 10 |
| 12 | `linked_event_id` | `str` | 25284 | 58 | High-cardinality string/identifier (58 unique) |
| 13 | `flexibility` | `str` | 0 | 4 | Distribution: `fixed`: 21138, `reducible`: 2682, `stoppable`: 1297, `reducible_or_stoppable`: 225 |
| 14 | `minimum_allowed_amount` | `float64` | 22435 | 301 | Range: [8.0, 810,350.0]<br>Has Negatives: False |

### 5.6 `request_payment_options.csv`
- **Dimensions**: 790 rows × 9 columns
- **Raw Header**: `payment_option_id,request_id,payment_method,payment_amount,number_of_payments,first_payment_date,payment_frequency_days,financing_fee,total_payable_amount`

| Column Order | Column Name | Inferred Dtype | Null Count | Unique Count | Value Characteristics & Bounds |
|---|---|---|---|---|---|
| 1 | `payment_option_id` | `str` | 0 | 790 | High-cardinality string/identifier (790 unique) |
| 2 | `request_id` | `str` | 0 | 275 | High-cardinality string/identifier (275 unique) |
| 3 | `payment_method` | `str` | 0 | 2 | Distribution: `installments`: 515, `full_payment`: 275 |
| 4 | `payment_amount` | `float64` | 0 | 787 | Range: [7.29, 83,923,000.0]<br>Has Negatives: False |
| 5 | `number_of_payments` | `int64` | 0 | 9 | Range: [1, 24]<br>Has Negatives: False |
| 6 | `first_payment_date` | `str` | 0 | 194 | Date Range: [2019-09-03, 2026-09-04]<br>Format: Consistent YYYY-MM-DD |
| 7 | `payment_frequency_days` | `float64` | 275 | 3 | Range: [28, 31]<br>Has Negatives: False |
| 8 | `financing_fee` | `float64` | 0 | 515 | Range: [0.0, 18,463,059.92]<br>Has Negatives: False |
| 9 | `total_payable_amount` | `float64` | 0 | 787 | Range: [166.61, 102,386,059.92]<br>Has Negatives: False |

### 5.7 `exchange_rates.csv`
- **Dimensions**: 134 rows × 4 columns
- **Raw Header**: `rate_date,from_currency,to_currency,rate`

| Column Order | Column Name | Inferred Dtype | Null Count | Unique Count | Value Characteristics & Bounds |
|---|---|---|---|---|---|
| 1 | `rate_date` | `str` | 0 | 39 | Date Range: [2023-10-15, 2026-11-15]<br>Format: Consistent YYYY-MM-DD |
| 2 | `from_currency` | `str` | 0 | 2 | Distribution: `USD`: 88, `EUR`: 46 |
| 3 | `to_currency` | `str` | 0 | 5 | Distribution: `INR`: 33, `IDR`: 30, `EUR`: 25, `USD`: 24, `ZAR`: 22 |
| 4 | `rate` | `float64` | 0 | 5 | Range: [0.92, 15,833.33]<br>Has Negatives: False |

### 5.8 `messages.csv`
- **Dimensions**: 215 rows × 7 columns
- **Raw Header**: `message_id,user_id,request_id,related_event_id,sent_at,source_type,message_text`

| Column Order | Column Name | Inferred Dtype | Null Count | Unique Count | Value Characteristics & Bounds |
|---|---|---|---|---|---|
| 1 | `message_id` | `str` | 0 | 215 | High-cardinality string/identifier (215 unique) |
| 2 | `user_id` | `str` | 0 | 215 | High-cardinality string/identifier (215 unique) |
| 3 | `request_id` | `str` | 87 | 128 | High-cardinality string/identifier (128 unique) |
| 4 | `related_event_id` | `str` | 176 | 39 | High-cardinality string/identifier (39 unique) |
| 5 | `sent_at` | `str` | 0 | 120 | Date Range: [2019-08-31T09:30:00Z, 2026-09-03T01:00:00Z]<br>Format: Consistent ISO-8601 (YYYY-MM-DDTHH:MM:SSZ) |
| 6 | `source_type` | `str` | 0 | 5 | Distribution: `employer`: 126, `service_provider`: 31, `financial_service`: 23, `bank`: 18, `merchant`: 17 |
| 7 | `message_text` | `str` | 0 | 215 | High-cardinality string/identifier (215 unique) |

### 5.9 `images.csv`
- **Dimensions**: 16 rows × 4 columns
- **Raw Header**: `image_id,user_id,request_id,related_event_id`

| Column Order | Column Name | Inferred Dtype | Null Count | Unique Count | Value Characteristics & Bounds |
|---|---|---|---|---|---|
| 1 | `image_id` | `str` | 0 | 16 | High-cardinality string/identifier (16 unique) |
| 2 | `user_id` | `str` | 0 | 16 | High-cardinality string/identifier (16 unique) |
| 3 | `request_id` | `str` | 0 | 16 | High-cardinality string/identifier (16 unique) |
| 4 | `related_event_id` | `str` | 0 | 16 | High-cardinality string/identifier (16 unique) |

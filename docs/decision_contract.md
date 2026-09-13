# Decision Contract

**Status:** Phase 0.3 deliverable. Normative.
**Scope:** Defines *what* the system must output and *under which rules*. It does not define *how* the code is organized — that is `architecture.md` (Phase 0.4).
**Sources:** `DNA.md` (specification) and `docs/data-profile.md` (observed dataset, 0.1).
**Consumers:** the planner, the deterministic verifier, the explanation builder, and the pre-submission validator.

Confidence is marked per rule:

- `[SPEC]` — stated directly in DNA.md. Non-negotiable.
- `[DERIVED]` — proven by exact reconciliation against the 25-row calibration set or the profile counts.
- `[ASSUMED]` — a working decision that the sample cannot settle. Every one of these is listed again in §13.

---

## 1. Output schema

One row per row of `requests.csv`. 250 rows. Header, verbatim and in this order:

```csv
request_id,amount_safe_to_pay,affordability_status,recommended_payment_method,payment_plan,earliest_date_for_full_payment,spending_changes_needed,decision_explanation
```

| Field | Type | Format | Empty allowed |
|---|---|---|---|
| `request_id` | string | as supplied in `requests.csv` | no |
| `amount_safe_to_pay` | number | plain numeric, no separators, no currency code | no |
| `affordability_status` | enum | 4 values, §6 | no |
| `recommended_payment_method` | enum | 5 values, §6 | no |
| `payment_plan` | string | §7 grammar, or `none` | no |
| `earliest_date_for_full_payment` | date | `YYYY-MM-DD` | **yes** — §6.3 |
| `spending_changes_needed` | string | §8 grammar, or `none` | no |
| `decision_explanation` | string | §11 template output | no |

Hard invariants, enforced by the validator before any file is written:

- `0 <= amount_safe_to_pay <= requested_amount` `[SPEC]`
- All monetary output is in the user's `home_currency` `[SPEC]`
- `affordable_now` ⟹ `earliest_date_for_full_payment == request_date` `[SPEC]`
- Row count is exactly 250 and `request_id` set matches `requests.csv` exactly `[SPEC]`

---

## 2. Forecast window and the safety test

**Window.** `request_date` through `request_date + 90 days`, inclusive. `[SPEC]`

**The safety test.** A candidate plan is *safe* if and only if, for every day in the window, the projected running balance is `>= minimum_balance_to_keep`, with the candidate's own payments applied on their scheduled dates, all protected and essential obligations applied on theirs, and confirmed income credited on its. `[SPEC]`

**Additional conditions for a plan to be recommendable** `[SPEC]`:

1. Every payment in the plan is itself affordable on its own date.
2. The plan completes the **full** `requested_amount` on or before `desired_completion_date`.
3. Protected expense categories are never sacrificed to make the plan work.

**Balance is derived, never stored.** `current_available_balance` is the opening value at `request_date`; every subsequent day is computed from it. `[SPEC]`

---

## 3. Cash-flow inclusion rules

`financial_events.csv` carries 25,342 rows across 8 `event_type` values, 6 `status` values, and 3 `direction` values. The inclusion decision is made on `(status, direction, event_type)`.

### 3.1 Inclusion matrix

| status | Rows | direction | Treatment |
|---|---|---|---|
| settled | 25,148 | debit / credit | **Include.** Historical fact; substrate for recurrence reconstruction (§4) |
| scheduled | 70 | debit | **Include.** Confirmed future obligation [SPEC] |
| scheduled | 70 | credit | **Include, pending inspection.** See below [ASSUMED-1, under verification] |
| pending | 71 | debit | **Include** as an encumbrance on its effective date [ASSUMED-2] |
| pending | 71 | credit | **Exclude.** Named explicitly in DNA.md [SPEC] |
| cancelled | 22 | any | **Exclude [SPEC]** |
| failed | 21 | any | **Exclude [SPEC]** |
| unrealized | 10 | non_cash | **Exclude [SPEC]** |

scheduled is not pending. They are distinct status values in this schema — 70 and 71 rows respectively. DNA.md's exclusion names pending credits only. It separately instructs forecasting from "confirmed future payments" and states that financial_events.csv contains "the next confirmed salary." A scheduled credit is confirmed; a pending credit carries settlement risk. The schema draws the line, not us. [SPEC]

Resolved by inspection, not policy. The phantom-liquidity risk — passing the safety check on income that never lands — is the most dangerous failure mode available to this system. But the entire disputed population is 70 rows. Rather than rule from theory, verification 4 enumerates all 70 and reports the event_type / category / direction breakdown. If scheduled credits are salary, the inclusion is proven. If any is speculative, it is excluded by name. This converts ASSUMED-1 into fact at a cost of one query. [VERIFY-4]

On unrealized. unrealized (10) = non_cash (10) = investment_valuation (10) — the same 10 rows. A single exclusion on status == 'unrealized' removes all of them. [DERIVED]

### 3.2 Sign convention

`amount` is **strictly positive everywhere** (min 2.0, max 48,830,000.0, zero negatives). Direction is carried solely by the `direction` column. `[DERIVED]`

```
debit    → balance decreases
credit   → balance increases
non_cash → excluded entirely, never touches the balance
```

Code must never infer direction from sign.

### 3.3 Which date to use — two distinct purposes

event_date and settlement_date are not interchangeable. Each field serves one purpose and must not be used for the other. [ACCEPTED-REVIEW]

Purpose	Field	Rationale
Cadence inference (§4) — deriving the recurrence interval of a series	event_date	Billing dates are regular by construction. Settlements shift around weekends and holidays, producing noise like 33 / 27 / 31 that corrupts interval inference and drifts projections across the 90-day boundary
Balance reconstruction (§2) — the day money actually moves	settlement_date, falling back to event_date on the 10 nulls	The balance changes when the transaction settles, not when it is billed

Using settlement_date for cadence would introduce mathematical noise into every projected series. Using event_date for balance would misdate every cash movement. Both errors are silent.

Profile support: event_date has 1,308 distinct values, settlement_date has 1,310, over identical ranges (2019-03-09 to 2026-09-03). They coincide on most rows — which is exactly why a naive implementation passes casual testing and fails on the rows that matter.

### 3.4 Duplicates

DNA.md orders that duplicate records be ignored, but `financial_events.csv` has **no duplicate flag column**. Detection must therefore be derived. Rule: two rows are duplicates when they share `(user_id, description, category, amount, currency, event_date, direction)` and differ only in `event_id`. Keep the lowest `event_id`; drop the rest. `[ASSUMED-4]`

This section is **conditional**. If the duplicate scan (verification 3) returns zero collisions, this logic is removed from the build entirely rather than carried as dead code.

### 3.5 Blank amounts
Exactly 16 rows had a null amount, all mapping 1:1 to images.csv. A blank amount is never zero. [SPEC]

Phase 0.2 complete. All 16 values were extracted from source PNGs and human-verified. They are frozen in src/buy_or_wait/data/image_amounts.json and merged into financial_events at load time. No vision model runs during scoring. [RESOLVED]

event_id | Amount | Currency | Note
event_253 | 4365000.00 | IDR | Net salary — feeds the income series
event_1442 | 100000.00 | INR | Lakh notation 1,00,000.00 normalized
event_1545 | 41272.00 | INR | 
event_1700 | 2870.00 | INR | Flagged — grand total cropped
event_1786 | 704.05 | INR | 
event_3051 | 1995.00 | INR | 
event_3231 | 8528.00 | INR | Flagged — rounded from 8528.10
event_4535 | 15339.00 | INR | 
event_5170 | 723.00 | INR | 
event_6033 | 79679.26 | INR | 
event_6859 | 3650.00 | INR | 
event_7307 | 33.50 | USD | Only non-INR/IDR of the set — FX applies (§5)
event_7941 | 2298.00 | INR | 
event_9421 | 4543.00 | INR | Rs/Ps column split 4543 00 normalized
event_9806 | 9968.00 | INR | 
event_10521 | 393.22 | INR | 

Normalization applied. Three values were not machine-parseable as extracted:

event_1442 — 1,00,000.00 is Indian lakh grouping, not a thousands separator. A naive separator strip yields the correct 100000.00, but a locale-aware parser could misread it. Hardcoded.
event_9421 — 4543 00 is a handwritten Rs./Ps. two-column receipt. The space is the decimal point. Verified against the line-item sum: 1500 + 724 + 796 + 550 + 303 + 670 = 4543.
event_7941 — 2,298 separator only.

Flag rationale.

event_1700 — the receipt's grand total is cropped off the image. The visible Item Bill is 2854.00, with a partial line of 16.00 below it. Under §10.1 rule 4, the financially safer interpretation of an ambiguous debit is the higher figure, so 2870.00 is used. Overstating a grocery outflow by 16 INR is negligible; understating it risks a false safety pass. [ASSUMED-12]

event_3231 — the bill prints an unrounded Total of 8528.10 and a payable Grand Total of 8528. The amount actually charged is authoritative. [ASSUMED-13]

event_253 is structurally significant. It is the only income row among the 16. Until resolved, user_03's salary series carried a gap, and recurrence reconstruction (§4) was projecting forward from incomplete history.

    Calibration overlap — highest-value test in the project. image_01, image_02, and image_03 link to request_03, request_16, and request_17 — all inside sample_requests.csv. Three image-dependent users have published ground truth. These three requests exercise image ingestion, FX, recurrence reconstruction, forecasting, ranking, and explanation generation end to end against known-correct output. They are the primary regression test.
---

## 4. Recurrence reconstruction

Highest-risk deterministic component in the build.

financial_events.csv has no is_recurring column and no recurrence-interval column. payment_frequency_days in request_payment_options.csv governs request financing only, not the user's existing obligations. Recurrence must be reconstructed from history. [DERIVED]

### 4.1 Series key
(user_id, description, category, direction)

description is semantic, not a generic transaction label. [DERIVED] The 164 distinct values are specific: "Outstanding telecom bill", "Property maintenance invoice", "EV charging wallet payment", "Bulk groceries and pantry purchase". Calibration explanations reference "the family streaming plan", "the weekend food delivery", "the online backup subscription" — all drawn from this field. These are not Card Purchase or ACH Transfer.

164 descriptions across 275 users means descriptions are a shared vocabulary, reused across users. Within a single user they are expected to be near-unique, which is why user_id leads the key.

Amount-based sub-clustering is explicitly rejected. [REJECTED-REVIEW] A tolerance band (e.g. ±5%) to split series by amount would:

introduce a magic constant with no basis in the data
split legitimate variable-amount series — utility bills routinely swing well beyond 5%
contradict the schema, since every reducible event carries a minimum_allowed_amount precisely because its amount is expected to vary

The stated failure mode — a user's streaming, gym, and electricity collapsing into one series — cannot occur. Those carry different description and different category (streaming, gym, utilities), both already in the key.

Validated empirically, not assumed. [VERIFY-5] Rather than guessing a threshold, count (user_id, description, category, direction) groups whose event_date gaps are bimodal — the signature of two interleaved series sharing a key. If the count is zero, the key is proven sufficient and no sub-clustering logic is written. If non-zero, the affected groups are inspected individually and a targeted rule is written for them. Evidence, not a constant.

### 4.2 Interval inference
Order the series by event_date (§3.3 — never settlement_date).
Compute the modal gap between consecutive occurrences.
Do not hardcode 30 days. Monthly cadence is expected to dominate, but weekly, fortnightly, and quarterly series must survive.
Require a minimum of 3 occurrences before declaring a series recurring. Two points define an interval but not a pattern. [ASSUMED-14]
### 4.3 Forward projection
Project from the last observed occurrence across the 90-day window.
Amount for each projected occurrence: the most recent settled amount in the series. [ASSUMED-5]
Apply each projected flow on its projected date; the balance test (§2) is evaluated daily.
### 4.4 Recurrence signals
Signal | Rows | Strength
---|---|---
 event_type == 'subscription' | 2,488 | Strong — recurring by definition
 event_type == 'debt_payment' | 567 | Strong
 event_type == 'income' and category == 'salary' | 1,690 | Strong — the salary series
 flexibility != 'fixed' | 4,204 | Strong — a one-off purchase has nothing to reduce or stop, so controllability implies commitment

Non-recurring by definition: refund (22), investment_valuation (10), investment_sale (5), investment_purchase (29).


---

## 5. Currency normalization

All output is in `home_currency`. `[SPEC]`

- 140 events carry `currency != home_currency`.
- All 140 resolve to an **exact dated rate** on `(rate_date == event_date, from_currency, to_currency)`. Zero gaps. `[DERIVED]`

**Rule:** exact-date lookup only. Do **not** implement rate interpolation, nearest-date fallback, or inverse-pair derivation — the data proves none is needed, and each would be a silent-error surface. If a lookup misses, that is a bug or a data change: fail loudly. `[DERIVED]`

Available directed pairs: `USD→INR`, `USD→IDR`, `USD→EUR`, `EUR→USD`, `EUR→ZAR`. Rates are directed; `from` and `to` are not interchangeable.

---

## 6. Status ↔ method legality

### 6.1 Eligibility gates

A payment method is *eligible* only if it clears every gate below. Gates are hard filters applied **before** ranking.

| Method | Gates |
|---|---|
| `full_payment` | `'full_payment' ∈ payment_methods_user_will_consider` `[SPEC]` |
| `partial_payment` | `'partial_payment' ∈ methods` **and** `allows_partial_payment == true` **and** `0 < amount_safe_to_pay < requested_amount` **and** `earliest_date_for_full_payment <= desired_completion_date` `[SPEC]` |
| `installments` | `'installments' ∈ methods` **and** at least one option exists in `request_payment_options.csv` **and** `number_of_payments <= max_installment_months` `[ASSUMED-6]` |
| `wait` | `'full_payment' ∈ methods` **and** full payment becomes safe later within the window `[SPEC]` |
| `not_recommended` | fallback when no eligible method is safe `[SPEC]` |

**Structural consequences from the profile** `[DERIVED]`:

- 112 of 275 users exclude `full_payment`. For them, `affordable_now` and `wait` are **structurally unreachable** regardless of balance.
- 170 of 250 requests have `allows_partial_payment == false`. `partial_payment` is live for at most 80 requests.
- `max_installment_months` is null for exactly 119 users = 60 (`full_payment` only) + 40 (`full_payment|partial_payment`) + 19 (`partial_payment` only). The null is an **implication of not considering installments**, not missing data. Treat null as "installments ineligible", never as "unbounded".
- Options offer 1–24 payments; `max_installment_months` ranges 2–12. Some supplied options are therefore ineligible for their own user. Do not assume a supplied option is usable.

### 6.2 The legality matrix

Reconciled exactly against the 25 calibration rows (3 + 9 + 6 + 7 = 25; 6 `full_payment` = 3 + 3; 3 non-`none` spending-change strings). `[DERIVED]`

| `recommended_payment_method` | `affordability_status` | `payment_plan` | `earliest_date_for_full_payment` | Spending changes |
|---|---|---|---|---|
| `full_payment` | `affordable_now` | one payment on `request_date` | `== request_date` | must be `none` |
| `full_payment` | `affordable_with_plan` | one payment on `request_date` | populated | one or more |
| `partial_payment` | `affordable_with_plan` | **exactly two** payments | populated, `<= desired_completion_date` | permitted |
| `installments` | `affordable_with_plan` | matches a supplied option exactly | populated | **permitted — see below** |
| `wait` | `affordable_later` | **one** future-dated payment of the full amount | populated, equals the plan date | permitted |
| `not_recommended` | `not_affordable` | `none` | **empty** | must be `none` |

**Installments + spending changes.** The calibration set shows all 5 installment rows with `spending_changes = none`. This is **not** a prohibition — it is an emergent result of the ranking order, where "require no spending changes" (rank 2) outranks "minimize total paid" (rank 3), so change-free installment plans win tie-breaks. The engine **must** generate installment-plus-spending-change candidates and let the comparator reject them. Five rows cannot establish a negative rule, and DNA.md explicitly allows installments and spending changes to co-occur under `affordable_with_plan`. `[SPEC]`

**`affordable_now` requires no changes.** `amount_safe_to_pay` is defined *before* optional spending changes. If the full amount is only safe after changes, it was by definition not safe on `request_date`, so the status is `affordable_with_plan`. `[SPEC]` + `[DERIVED]`

### 6.3 When `earliest_date_for_full_payment` is empty

`earliest_date_for_full_payment` is empty when full payment never becomes safe without spending changes inside the 90-day window. `not_affordable` always implies empty. `affordable_with_plan` MAY be empty when the plan depends on spending changes. `[REVISED — 6 evaluation rows; the calibration set contains no such case]`

This field measures **financial capacity, independent of the user's method preferences**. It may equal `request_date` even when the recommendation is `installments`, because the user declined to consider full payment. It is computed **without** optional spending changes. `[SPEC]`

---

## 7. `amount_safe_to_pay`

**Definition.** The largest amount the user can pay on `request_date` **before any optional spending changes** while passing the §2 safety test for the full 90-day window, capped at `requested_amount`. `[SPEC]`

Consequences:

- **`0.0` is legal and mandatory** when the opening balance is at or below `minimum_balance_to_keep`, or when any payment today would breach the floor later in the window. There is **no artificial floor**. The calibration minimum of 83.05 is a property of those 25 users, not a rule.
- It is a **capacity measure, not a recommendation.** It is populated even when `affordability_status == 'not_affordable'` — two calibration rows state an available amount while refusing the request.
- It is computed **before** spending changes even when the chosen plan uses them.

### 7.1 `payment_plan` grammar

```
<YYYY-MM-DD>:<amount>|<YYYY-MM-DD>:<amount>|...
```

Chronological order. `none` when no payment is recommended. `[SPEC]`

Amount rendering inside the plan `[DERIVED]`:

- No thousands separators. No currency code.
- Whole numbers render with no decimal point: `25256`, `68432`, `12693000`
- Non-whole numbers render with **exactly two** decimals, trailing zeros preserved: `620.40`, `996.60`, `15952906.67`, `23.50`

Per-method plan construction:

- **`full_payment`** — one entry: `request_date:requested_amount`
- **`wait`** — one entry: `earliest_date_for_full_payment:requested_amount`. **Not** `none`. `[DERIVED]`
- **`partial_payment`** — exactly two entries: `request_date:amount_safe_to_pay` then `earliest_date_for_full_payment:(requested_amount - amount_safe_to_pay)`. The two must sum to exactly `requested_amount`. Does not need to match any supplied option. `[SPEC]`
- **`installments`** — must match a supplied option exactly. Dates are `first_payment_date + k * payment_frequency_days` for `k = 0 .. number_of_payments - 1`; every amount is that option's `payment_amount`. `[SPEC]`
- **`not_recommended`** — `none`

**Installment date generation is verified.** All 5 calibration installment plans reproduce exactly under `first_payment_date + k * payment_frequency_days`, with observed frequencies of 28, 30, and 31 days. `[DERIVED]`

**Option arithmetic is exact.** Across all 790 options, zero mismatches on both `total_payable_amount == requested_amount + financing_fee` and `total_payable_amount == payment_amount * number_of_payments`. Use the supplied fields directly; do not recompute or round. `[DERIVED]`

---

## 8. Spending changes

### 8.1 Grammar

```
stop:<event_id>
reduce_to:<event_id>:<new_amount>
```

Up to **three**, separated by `|`. `none` when no change is needed. `[SPEC]`

### 8.2 Eligibility

A change is legal only when **all** of the following hold:

1. The event is **recurring** (§4). One-time purchases cannot be stopped or reduced. `[SPEC]`
2. `flexibility` permits the operation `[DERIVED]`:

   | `flexibility` | Rows | `stop` | `reduce_to` |
   |---|---|---|---|
   | `fixed` | 21,138 | no | no |
   | `reducible` | 2,682 | no | yes |
   | `stoppable` | 1,297 | yes | no |
   | `reducible_or_stoppable` | 225 | yes | yes — **but not both on the same event** |

3. The event's `category` appears in the user's `expense_categories_user_is_willing_to_stop` (for `stop`) or `expense_categories_user_is_willing_to_reduce` (for `reduce_to`). A null list means **no changes of that type are permitted** for that user — 62 users permit no stops, 39 permit no reductions. `[SPEC]`
4. The event's `category` is **not** in `expense_categories_to_protect`. `[SPEC]`
5. `stop` and `reduce_to` on the **same** `event_id` are mutually exclusive. If both types are needed, they must reference **different** events. `[SPEC]`

### 8.3 The `reduce_to` target

`new_amount` is always the event's `minimum_allowed_amount`. `[ASSUMED-7]`

Supporting evidence: `minimum_allowed_amount` is non-null on exactly 2,907 rows = 2,682 `reducible` + 225 `reducible_or_stoppable`. Exact correspondence with the reducible population. `[DERIVED]` It is the schema-defined floor, and any other value is unscoreable against a deterministic ground truth.

`new_amount` renders under the §7.1 numeric rule: `665950`, `23.50`.

### 8.4 Which `event_id` to cite
A recurring obligation spans many rows; the change string cites exactly one event_id.

Rule: cite the most recent occurrence in the series, as of request_date, whose row carries the metadata authorizing the operation. [ASSUMED-8, revised]

- redu`ce_to → the row must have a non-null minimum_allowed_amount
- stop → the row's flexibility must be stoppable or reducible_or_stoppable

The metadata lives on settled historical rows, not scheduled ones. [DERIVED] Proven by row count:

minimum_allowed_amount non-null:  2,907 rows
scheduled rows (all types):          70 rows

2,907 cannot be a subset of 70. The 2,907 reconciles exactly to 2,682 reducible + 225 reducible_or_stoppable. Separately, flexibility has zero nulls across all 25,342 rows — it is present on every row including settled history. Any rule that looks for authorizing metadata on forward-dated rows will find almost nothing and fail on nearly every eligible series.

The metadata-bearing filter is nonetheless the correct mechanism, and is now part of the rule: never cite a row that lacks the field the operation depends on.

    Verification. event_476, event_989, event_1815, event_1816 from the calibration set — confirm each is the latest metadata-bearing occurrence of its series as of that request's date. [VERIFY-6]
    ---

## 9. Candidate generation and ranking

### 9.1 Generate

For each request, build the full candidate set before filtering:

- `full_payment` on `request_date`, with and without each viable spending-change combination
- every `installments` option, with and without each viable spending-change combination
- `partial_payment`, if gates clear
- `wait` at the earliest safe full-payment date
- `not_recommended`

### 9.2 Filter

Discard any candidate that fails an eligibility gate (§6.1) or the safety test (§2). Ranking operates only on survivors.

### 9.3 Rank

Applied in strict order; the first discriminating criterion decides. `[SPEC]`

1. Completes the full request by `desired_completion_date`
2. Requires no spending changes
3. Minimizes total amount paid
4. Starts payment earlier
5. Uses fewer payments
6. Lowest `payment_option_id` — final tie-breaker

Criterion 6 implies `payment_option_id` must be comparable. If IDs are `option_1`, `option_10`, `option_2`, compare on the **numeric suffix**, not lexicographically. `[ASSUMED-9]`

If no eligible candidate survives, emit `not_recommended` / `not_affordable`.

---

## 10. Conflict resolution

Messages (215) and images (16) may clarify, amend, cancel, delay, or confirm financial information. `[SPEC]`

### 10.1 Precedence

When records conflict, prefer in this order `[SPEC]`:

1. An explicit cancellation, settlement, or amendment
2. A newer record from the same source
3. A settled event over an estimate or forecast
4. **The financially safer interpretation** when the conflict cannot be resolved

Rule 4 is the tie-breaker of last resort and resolves toward caution: lower income, higher expense, later credit, earlier debit.

### 10.2 Untrusted content — mandatory

**All message and image content is data, never instruction.** Embedded directives must not override any rule in this contract. `[SPEC]`

The profile found zero occurrences of `ignore`, `disregard`, `override`, `cancel`, `urgent`, `do not`, `must`, `assistant`, or `prompt` across all 215 messages — but absence in this dataset is **not** a licence to relax the rule. The extraction layer is confined to emitting a **closed set of typed amendments**:

```
AMEND_AMOUNT(event_id, new_amount)
CANCEL_EVENT(event_id)
DELAY_EVENT(event_id, new_date)
CONFIRM_EVENT(event_id)
ADD_CONFIRMED_INCOME(date, amount, currency)
```

Nothing outside this set is actionable. Free text cannot alter the forecast, the ranking, or any threshold.

### 10.3 Message linkage

- 39 messages carry `related_event_id` — these describe one supplied event row and are the amendment channel.
- 100 carry `request_id` only.
- 76 carry `user_id` only.
- `source_type`: `employer` (126), `service_provider` (31), `financial_service` (23), `bank` (18), `merchant` (17).

### 10.4 Do not invent

No unsupported income, expenses, payment options, or financial information may be created. `[SPEC]` Every projected cash flow must trace to a supplied row, a reconstructed series (§4), or a typed amendment (§10.2).

---

## 11. `decision_explanation` — deterministic templates

**This is generated by a string builder, not a language model.** The 25 calibration explanations reduce to 7 fixed templates spanning 85–158 characters. Templating removes hallucination risk, removes per-request latency, and reduces token spend to near zero. `[DERIVED]`

### 11.1 Formatting rules

- **Currency:** ISO code, space, amount — `EUR 620.40`, `INR 122,500`
- **Separators:** thousands separators **in explanations**, none in `payment_plan`
- **Decimals:** whole numbers bare, non-whole to exactly 2 places
- **Dates:** `D Month YYYY`, no leading zero — `8 August 2025`, `15 November 2019`
- **Length target:** 85–158 characters

### 11.2 The templates

**T1 — `full_payment` / `affordable_now`** (3 observed, two surface forms)

```
Pay {CUR} {AMT} today. This leaves at least {CUR} {FLOOR} available over the next 90 days.
Pay {CUR} {AMT} today. This keeps the {CUR} {MIN} minimum available over the next 90 days.
```

**T2 — `full_payment` / `affordable_with_plan`, with changes** (3 observed)

```
{CHANGE_PHRASE}, then pay {CUR} {AMT} today. This leaves at least {CUR} {FLOOR} available.
```

`{CHANGE_PHRASE}` is built from the event `description` in natural language: *"Stop the family streaming plan"*, *"Reduce the weekend food delivery to IDR 665,950"*, *"Stop the online backup subscription and reduce the streaming subscription to USD 23.50"*. Two changes join with `and`.

**T3 — `installments` / `affordable_with_plan`** (5 observed)

```
Use {N} installments of {CUR} {PMT}, starting {DATE}. This leaves at least {CUR} {FLOOR} available.
```

**T4 — `wait` / `affordable_later`** (6 observed, two forms)

```
Pay {CUR} {AMT} in full on {DATE}. Paying earlier would take the balance below the {CUR} {MIN} minimum.
Wait until {DATE}, then pay {CUR} {AMT} in full. Paying sooner would put the {CUR} {MIN} minimum at risk.
```

**T5 — `partial_payment` / `affordable_with_plan`** (1 observed)

```
Pay {CUR} {AMT1} today and the remaining {CUR} {AMT2} on {DATE}. This completes the full request and keeps the {CUR} {MIN} minimum protected.
```

**T6 — `not_recommended` / `not_affordable`, no capacity today** (5 observed)

```
Do not make this payment by {DATE}. None of the available options keeps the {CUR} {MIN} minimum protected.
```

**T7 — `not_recommended` / `not_affordable`, capacity exists but cannot complete** (2 observed)

```
Do not proceed with the {CUR} {AMT} request. Although {CUR} {SAFE} is available today, the full amount cannot be completed safely within 90 days.
```

### 11.3 Slot definitions

| Slot | Source |
|---|---|
| `{CUR}` | `home_currency` |
| `{AMT}` | `requested_amount` |
| `{AMT1}` / `{AMT2}` | `amount_safe_to_pay` / remainder |
| `{SAFE}` | `amount_safe_to_pay` |
| `{MIN}` | `minimum_balance_to_keep` |
| `{FLOOR}` | forecast trough over the 90-day window under the chosen plan `[ASSUMED-10]` |
| `{N}`, `{PMT}` | option `number_of_payments`, `payment_amount` |
| `{DATE}` | context-dependent: T3 `first_payment_date`; T4 `earliest_date_for_full_payment`; T5 second payment date; T6 `desired_completion_date` `[ASSUMED-11]` |

**`{FLOOR}` vs `{MIN}`.** T1's two surface forms differ by whether the trough sits above the minimum ("leaves at least {FLOOR}") or exactly on it ("keeps the {MIN} minimum"). Selection rule: use the minimum-form when `FLOOR == MIN`, otherwise the floor-form. `[ASSUMED-10]`

---

## 12. Validator assertions

Every assertion must pass before `output.csv` is written. A failure is a **build stop**, not a warning.

**Schema**

1. Exactly 250 rows; `request_id` set matches `requests.csv` exactly
2. Header matches §1 byte for byte
3. No field is null except `earliest_date_for_full_payment`

**Value legality**

4. `affordability_status` ∈ the 4 allowed values
5. `recommended_payment_method` ∈ the 5 allowed values
6. `0 <= amount_safe_to_pay <= requested_amount`
7. The (status, method) pair appears in the §6.2 matrix

**Plan integrity**

8. `payment_plan` parses under the §7.1 grammar; dates are `YYYY-MM-DD`; order is chronological
9. `full_payment` ⟹ one payment, dated `request_date`, equal to `requested_amount`
10. `wait` ⟹ one payment, dated `earliest_date_for_full_payment`, equal to `requested_amount`
11. `partial_payment` ⟹ exactly two payments summing to exactly `requested_amount`; first dated `request_date` and equal to `amount_safe_to_pay`
12. `installments` ⟹ dates, count, and amounts reproduce a real `payment_option_id` exactly
13. `not_recommended` ⟹ `payment_plan == 'none'`
14. Every plan completes by `desired_completion_date`, except `not_recommended`

**Date integrity**

15. `affordable_now` ⟹ `earliest_date_for_full_payment == request_date`
16. `not_affordable` ⟹ `earliest_date_for_full_payment` empty
17. All other statuses ⟹ populated and within the 90-day window, unless the plan depends on spending changes

**Spending changes**

18. Parses under §8.1; at most 3 changes
19. Every cited `event_id` exists and belongs to this `user_id`
20. Operation is permitted by that event's `flexibility`
21. Category is in the user's corresponding willingness list and **not** in `expense_categories_to_protect`
22. No `event_id` appears with both `stop` and `reduce_to`
23. `affordable_now` and `not_affordable` ⟹ `spending_changes_needed == 'none'`

**Explanation**

24. Matches one of the 7 templates for the emitted (status, method) pair
25. Every number and date in the text agrees with the structured fields in the same row

**Preference honouring**

26. The emitted method is in `payment_methods_user_will_consider` (where `wait` is gated on `full_payment` per §6.1, not on a literal "wait" token), or is `not_recommended`
27. `partial_payment` ⟹ `allows_partial_payment == true`
28. `installments` ⟹ `number_of_payments <= max_installment_months`

**Data completeness**
29. All 16 formerly-blank events resolve to a non-null positive amount from
    image_amounts.json at load time; a null survivor is a build stop
30. Cadence inference reads event_date only; balance reconstruction reads
    settlement_date with event_date fallback — never the reverse
31. Every cited event_id in spending_changes_needed carries the metadata its
    operation requires (non-null minimum_allowed_amount for reduce_to;
    stoppable or reducible_or_stoppable flexibility for stop)
32. No scheduled credit enters the forecast unless it appears on the
    inspected-and-approved list from VERIFY-4
33. requests 03, 16, and 17 reproduce their sample_requests.csv ground truth
    exactly across all seven output fields

---

## 13. Open assumptions register

Every `[ASSUMED]` in this document, with its resolution path. These are the failure surface.
Assumption | Impact | Resolution
---|---|---
1 | scheduled credits included | High — phantom liquidity | VERIFY-4 — enumerate all 70
2 | Pending debits in, pending credits out | Medium | Ruled. DNA.md isolates credits
3 | settlement_date preferred | — | SUPERSEDED. Split by purpose, §3.3
4 | Duplicate detection key | Low | VERIFY-3 — delete the logic if zero collisions
5 | Projected amount = latest settled amount | High | Check within-series amount variance
6 | number_of_payments <= max_installment_months | Medium | Confirm against a long-option calibration user
7 | reduce_to = minimum_allowed_amount | High — direct scoring | VERIFY-1 — event_989 = 665950, event_1816 = 23.50
8 | Latest metadata-bearing occurrence cited | High — direct scoring | VERIFY-6 — revised per review
9 | payment_option_id compared numerically | Low | Inspect the ID format
10 | {FLOOR} = forecast trough; form by FLOOR == MIN | Medium | Recompute 25 calibration troughs
11 | {DATE} slot sources per template | Medium | Same recomputation
12 | event_1700 = 2870.00 | Low — 16 INR, one user | Unresolvable; source cropped. Safer-interpretation rule applied
13 | event_3231 = 8528.00 | Low — 0.10 INR | Unresolvable; both figures printed. Charged amount wins
14 | Minimum 3 occurrences to declare a series | Medium | Sweep 2 vs 3 vs 4 against calibration
16 | T7 threshold of 10% | Low — explanation tone | Fitted to 7 calibration rows, adopted because decision_explanation is scored on usefulness rather than exact match and no other discriminator exists

### Pending verifications

| # | Question | Settles | Cost |
|---|---|---|---|
| 1 | `minimum_allowed_amount` for `event_989`, `event_1816` | ASSUMED-7 | One lookup |
| 2 | Does event history extend past `request_date`? | Lookahead legitimacy vs. leakage | One query |
| 3 | Exact `(user_id, amount, event_date, description)` collision count | ASSUMED-4; possible deletion of §3.4 | One query |
| 4 | Full breakdown of all 70 scheduled rows | ASSUMED-1 — the phantom-liquidity risk | One query |
| 5 | Count of series keys with bimodal event_date gaps | §4.1 key sufficiency | One query |
| 6 | Series position of event_476, event_989, event_1815, event_1816 | ASSUMED-8 | One query |

---

## 14. Cost posture

Recorded here because `evaluation/usage_report.md` is a scored deliverable.
Deterministic — zero model calls: forecasting, safety test, candidate generation, ranking, plan construction, spending-change selection, explanation text, validation.

Job | Volume | Status
---|---|---
Image amount extraction | 16 | DONE — frozen to image_amounts.json. Never re-runs.
Message → typed amendment | ≤ 215, one-time | Cacheable; only the 39 event-linked messages may be required

Scoring-time model calls: zero. Both extraction jobs produce cached structured artifacts. The run that produces output.csv reads the cache and calls nothing.

---

## 15. Change log

| Version | Change |
|---|---|
| 0.1 | Initial contract. Invariant "installments implies no spending changes" **removed** following review — it was an overfit to 5 calibration rows and contradicts DNA.md. `amount_safe_to_pay = 0.0` explicitly permitted. A/B/C ruled: `reduce_to` = `minimum_allowed_amount`; no hardcoded payment count; pending debits included. Gaps added for `scheduled` status and undetectable duplicates. |
| 0.2 | Phase 0.2 resolved — 16 image amounts extracted, human-verified, frozen to image_amounts.json; §3.5 completeness block lifted; 2 values flagged (ASSUMED-12, -13); requests 03/16/17 identified as the end-to-end ground-truth test. Review rulings — ACCEPTED: event_date/settlement_date split by purpose (§3.3, supersedes ASSUMED-3); metadata-bearing-row filter for spending-change citation (§8.4). REJECTED: amount-band sub-clustering in §4.1 (magic constant, splits legitimate variable-amount series, premise contradicted by observed description semantics); scheduled-credit exclusion by policy (2,907 vs 70 row count refutes the premise; resolved by inspection as VERIFY-4 instead). Verifications expanded from 3 to 6. |
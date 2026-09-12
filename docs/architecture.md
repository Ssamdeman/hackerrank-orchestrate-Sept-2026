# Architecture

**Status:** Phase 0.4 deliverable. Normative for structure; `decision-contract.md` is normative for rules.
**Scope:** How the system is organized, what each module owns, what flows between them, and in what order it is built.
**Reads with:** `DNA.md` (problem), `docs/data-profile.md` (observed data), `docs/decision-contract.md` (decision rules), `docs/image-extraction.md` (Phase 0.2 evidence).

---

## 1. Design stance

**The engine is deterministic. Models are confined to the perception edge.**

Scoring is on numeric and categorical accuracy against hidden ground truth, and every decision rule in DNA.md is fully specified. Nothing about forecasting, safety testing, ranking, or explanation generation benefits from a language model — each would only add variance, latency, and cost to a problem that has an exact answer.

Three consequences shape everything below:

1. **Models parse; they never decide.** Extraction converts unstructured input into a closed set of typed records. Those records then flow through pure Python. No model output ever reaches a threshold, a comparison, or an output field directly.
2. **Extraction runs once, offline, and is frozen.** Image amounts are already frozen. Message amendments will be. The scoring run makes **zero model calls**.
3. **The validator is a peer of the planner, not a postscript.** Output that violates the contract never reaches disk. Failures stop the build rather than degrade quietly.

### 1.1 Fail loud

Every silent-failure surface is converted to an exception:

- An FX lookup that misses → raise. The data proves zero gaps (§5, contract); a miss means a bug or changed data.
- A formerly-blank amount still null after merge → raise.
- A candidate plan that passes ranking but fails validation → raise.
- A series with fewer occurrences than the recurrence threshold → excluded explicitly, logged, never silently projected.

A wrong number that looks plausible costs more than a crash.

---

## 2. Repository layout

```
.
├── DNA.md
├── main.py                          # entry point — thin, arg parsing + pipeline call
├── pyproject.toml                   # uv, src-layout, Python 3.14
├── README.md
├── docs/
│   ├── layout.md
│   ├── data-profile.md              # Phase 0.1
│   ├── image-extraction.md          # Phase 0.2 evidence
│   ├── decision-contract.md         # Phase 0.3 — the rules
│   └── architecture.md              # this file
├── dataset/                         # READ-ONLY, never written
│   ├── requests.csv
│   ├── output.csv
│   ├── sample_requests.csv
│   ├── financial_profiles.csv
│   ├── financial_events.csv
│   ├── request_payment_options.csv
│   ├── exchange_rates.csv
│   ├── messages.csv
│   ├── images.csv
│   └── media/images/
├── src/
│   ├── __init__.py
│   ├── config.py                    # paths, constants, forecast horizon
│   ├── models.py                    # frozen dataclasses — the shared vocabulary
│   ├── data/
│   │   ├── image_amounts.json       # FROZEN — 16 verified amounts
│   │   └── message_amendments.json  # FROZEN — typed amendments (Phase 2)
│   ├── io/
│   │   ├── loaders.py               # CSV → dataclasses, schema validation
│   │   └── writer.py                # output.csv emission + formatting
│   ├── state/
│   │   ├── fx.py                    # exact-date currency normalization
│   │   ├── amendments.py            # apply typed amendments to events
│   │   └── recurrence.py            # series detection + forward projection
│   ├── forecast/
│   │   └── engine.py                # daily balance projection, 90-day window
│   ├── planner/
│   │   ├── candidates.py            # generate the full candidate set
│   │   ├── spending.py              # legal spending-change combinations
│   │   └── ranking.py               # the six-level comparator
│   ├── verify/
│   │   ├── safety.py                # the 90-day safety test
│   │   └── validator.py             # the 33 contract assertions
│   ├── explain/
│   │   ├── templates.py             # the 7 explanation templates
│   │   └── formatting.py            # currency, separator, date rendering
│   └── llm/                         # OFFLINE ONLY — never called at scoring time
│       ├── extract_images.py        # DONE, superseded by frozen JSON
│       └── extract_messages.py      # Phase 2
├── scripts/
│   ├── profile_dataset.py           # Phase 0.1
│   └── verify_*.py                  # the six verification queries
├── tests/
│   ├── test_calibration.py          # all 25 sample_requests, exact match
│   ├── test_contract.py             # the 33 validator assertions
│   └── test_formatting.py           # number and date rendering
└── evaluation/
    └── usage_report.md              # scored deliverable
```

**`dataset/` is read-only.** No module opens it for writing. Enforced by convention and asserted in `loaders.py`.

---

## 3. Pipeline

Linear. Each stage consumes typed objects and emits typed objects. No stage reaches backward.

```
                 ┌─────────────────────────────────────────────┐
                 │ OFFLINE — runs once, output frozen to disk   │
                 │                                             │
                 │  PNGs ──► vision model ──► image_amounts.json│
                 │  messages ──► model ──► message_amendments   │
                 └─────────────────────────────────────────────┘
                                      │  (JSON only)
                                      ▼
  dataset/*.csv ──► [1] LOAD ──► [2] NORMALIZE ──► [3] RECONSTRUCT
                                                          │
                                                          ▼
                                                   [4] FORECAST
                                                          │
                                                          ▼
                          [5] GENERATE ──► [6] TEST ──► [7] RANK
                                                          │
                                                          ▼
                                                   [8] EXPLAIN
                                                          │
                                                          ▼
                                                  [9] VALIDATE
                                                          │
                                            pass ─────────┴───────── fail
                                              │                        │
                                              ▼                        ▼
                                        output.csv                  STOP
```

### Stage contracts

| # | Stage | Module | In | Out |
|---|---|---|---|---|
| 1 | Load | `io/loaders.py` | 9 CSVs | typed records, schema-checked |
| 2 | Normalize | `state/fx.py`, `state/amendments.py` | raw events | home-currency events, amendments applied |
| 3 | Reconstruct | `state/recurrence.py` | events | recurring series with intervals |
| 4 | Forecast | `forecast/engine.py` | series + confirmed flows | daily balance, 90 days |
| 5 | Generate | `planner/candidates.py`, `planner/spending.py` | request + profile + options | full candidate set |
| 6 | Test | `verify/safety.py` | candidates + forecast | safe candidates only |
| 7 | Rank | `planner/ranking.py` | safe candidates | one winner |
| 8 | Explain | `explain/templates.py` | winner + forecast | explanation string |
| 9 | Validate | `verify/validator.py` | all 250 rows | pass, or stop |

---

## 4. Module responsibilities

### 4.1 `io/loaders.py`

Owns every read from `dataset/`. Nothing else opens a CSV.

- Parses all 9 files into frozen dataclasses
- Merges `image_amounts.json` into `financial_events` by `event_id`
- **Raises** if any of the 16 formerly-blank amounts is still null (assertion 29)
- Validates observed schema against `data-profile.md`: column names, enum membership, row counts. A new enum value is a raise, not a shrug.
- Parses pipe-delimited preference fields into frozensets
- **Null semantics:** `max_installment_months` null ⟹ installments ineligible, never unbounded. `expense_categories_user_is_willing_to_*` null ⟹ that change type is forbidden for the user.

### 4.2 `state/fx.py`

Exact-date lookup only. Keyed on `(rate_date, from_currency, to_currency)`.

No interpolation, no nearest-date fallback, no inverse-pair derivation. The profile proves all 140 foreign-currency events resolve exactly. A miss **raises**.

Rates are directed. `USD→EUR` and `EUR→USD` are separate rows and are not each other's reciprocal.

### 4.3 `state/amendments.py`

Applies the closed amendment set from §10.2 of the contract:

```
AMEND_AMOUNT(event_id, new_amount)
CANCEL_EVENT(event_id)
DELAY_EVENT(event_id, new_date)
CONFIRM_EVENT(event_id)
ADD_CONFIRMED_INCOME(date, amount, currency)
```

Nothing outside this set is actionable. Free text never reaches this module — only typed records from the frozen JSON.

Conflict precedence (contract §10.1) is resolved here, terminating in the financially-safer interpretation: lower income, higher expense, later credit, earlier debit.

### 4.4 `state/recurrence.py`

The highest-risk module. Owns series detection and forward projection.

- Series key: `(user_id, description, category, direction)`
- Interval inferred from **`event_date`** modal gap — never `settlement_date`
- Minimum 3 occurrences to declare a series
- Projects forward across the window using the latest settled amount
- Excludes `refund`, `investment_valuation`, `investment_sale`, `investment_purchase` as non-recurring by definition

**`amount` is excluded from the series key, deliberately.** `[REJECTED-REVIEW]`

Keying on amount would shatter every variable-amount series into singletons.
Each fragment then falls below the 3-occurrence threshold and is dropped from
the forecast entirely — the obligation disappears, the projected balance rises,
and the safety check passes on headroom that does not exist. This is the
phantom-liquidity failure mode, arrived at from the opposite direction.

Every `reducible` event carries a `minimum_allowed_amount` specifically
because its amount is expected to vary. Amount instability is a documented
property of this data, not noise to key around.

A tolerance band is also not a key. Keys hash on exact equality; a variance
threshold is a clustering algorithm with a magic constant.

**VERIFY-5 is a hard gate on Phase 3.** It counts series keys with bimodal
`event_date` gaps — the signature of two interleaved series sharing a key.
Zero means the key is proven and no further logic is written. Non-zero means
the affected groups are inspected by hand and a targeted rule is written for
them specifically. No constant is introduced without evidence that one is
needed.

### 4.5 `forecast/engine.py`

Pure function. Same inputs, same output, always.

```python
def project(
    opening_balance: Decimal,
    start: date,
    horizon_days: int,
    flows: Sequence[Flow],
) -> BalanceCurve
```

- Day-resolution, `request_date` through `request_date + 90`, inclusive
- Balance is **derived from flows**, never stored or carried
- Applies flows on `settlement_date`, falling back to `event_date`
- `BalanceCurve` exposes `trough()` and `trough_date()` — both consumed by the explanation builder for the `{FLOOR}` slot

The engine knows nothing about affordability. It projects balances; the safety module judges them.

### 4.6 `planner/candidates.py`

Generates the **full** candidate set before any filtering:

- `full_payment` on `request_date`, with and without each viable spending-change combination
- Every `installments` option, with and without each viable spending-change combination
- `partial_payment`, if gates clear
- `wait` at the earliest safe full-payment date
- `not_recommended`

Installment dates are generated as `first_payment_date + k * payment_frequency_days`. Verified: all 5 calibration installment plans reproduce exactly under this rule at frequencies 28, 30, and 31.

**Generation is deliberately over-inclusive.** Installments combined with spending changes must be generated even though the calibration set shows none — their absence there is an emergent result of ranking rule 2, not a prohibition. Filtering is the filter's job.

### 4.7 `planner/spending.py`

Enumerates legal spending-change combinations, up to 3.

Gate chain, applied in order:

1. Event is recurring (§4.4)
2. `flexibility` permits the operation
3. `category` is in the user's corresponding willingness list
4. `category` is **not** in `expense_categories_to_protect`
5. `stop` and `reduce_to` never target the same `event_id`

`reduce_to` target is always `minimum_allowed_amount`. Cited `event_id` is the latest **metadata-bearing** occurrence as of `request_date` — a row without the field its operation depends on is never cited.

### 4.8 `verify/safety.py`

The single source of truth for "is this safe."

```python
def is_safe(candidate: Candidate, context: UserContext) -> SafetyResult
```

Returns pass/fail plus the trough and its date. A candidate is safe only when the balance never falls below `minimum_balance_to_keep` on any day in the window, with the candidate's payments applied, protected expenses intact, and confirmed income credited.

Also computes the two contract quantities, both **before** optional spending changes:

- `amount_safe_to_pay` — binary search on payment size against the safety test, capped at `requested_amount`, floor of `0.0` permitted and required when the opening balance is already at or below the minimum
- `earliest_date_for_full_payment` — forward scan for the first date the full amount passes, independent of the user's method preferences

### 4.9 `planner/ranking.py`

The six-level comparator, applied in strict order:

1. Completes the full request by `desired_completion_date`
2. Requires no spending changes
3. Minimizes total amount paid
4. Starts payment earlier
5. Uses fewer payments
6. Lowest `payment_option_id` — compared on **numeric suffix**, not lexicographically

Implemented as a sort key tuple, not a chain of conditionals. First discriminating criterion decides; no eligible survivor means `not_recommended`.

### 4.10 `explain/`

`templates.py` holds the 7 templates. `formatting.py` owns rendering, and the split matters because the two contexts differ:

| Context | Separators | Currency code | Example |
|---|---|---|---|
| `payment_plan` | none | none | `15952906.67` |
| `decision_explanation` | thousands | ISO prefix | `IDR 15,952,906.67` |

Shared rules: whole numbers render bare; non-whole to exactly two decimals with trailing zeros preserved. Dates in explanations are `D Month YYYY`, no leading zero.

Every number in the explanation is passed in from the structured fields of the same row — never re-derived, never reformatted from a string. Assertion 25 checks this.

### 4.11 `verify/validator.py`

Runs all 33 assertions across all 250 rows before a single byte reaches disk. Any failure is a stop with the offending `request_id` and assertion number.

Grouped: schema (1–3), value legality (4–7), plan integrity (8–14), date integrity (15–17), spending changes (18–23), explanation (24–25), preference honouring (26–28), data completeness (29), and the v0.2 additions (30–33).

### 4.12 `llm/` — the quarantine

Everything model-touching lives here and **runs offline only**. Enforced structurally: no module outside `llm/` imports an API client, and `main.py` has no code path that reaches it.

| Job | Volume | Status |
|---|---|---|
| Image extraction | 16 | Done. Frozen to `image_amounts.json`. Never re-runs. |
| Message → amendment | ≤ 215, one-time | Phase 2. Output frozen to `message_amendments.json`. |

Scoring-time model calls: **zero**.

### 4.13 `request_text` — audited, not parsed

`requests.csv` carries `request_text`, 250 distinct values. The architecture
does not route it to any decision module. This is a deliberate exclusion,
recorded here so it is a decision rather than an oversight.

**Evidence.** All 25 calibration texts restate structured fields — the amount,
often the deadline, and a question framing ("how much can I safely pay",
"now or wait", "the full amount"). None introduces a constraint absent from
`requested_amount`, `desired_completion_date`, `allows_partial_payment`, or
`payment_methods_user_will_consider`.

**Why not an extraction step.** DNA.md specifies no rule for a textual
constraint that contradicts the profile. Acting on one would require inventing
precedence policy, which §10.4 of the contract forbids. It would also add
250 model calls to a pipeline that currently makes zero at scoring time.

**VERIFY-7 — deterministic audit, no model.** Scan all 250 `request_text`
values and report:

1. Every currency amount in the text, compared against `requested_amount`
2. Every date in the text, compared against `desired_completion_date`
3. Substring hits on method language: `installment`, `partial`, `full`,
   `wait`, `split`, `upfront`, `refuse`, `prefer`, `only`

If the amounts and dates agree everywhere and no method language contradicts
the profile, `request_text` is confirmed decorative and this section stands
as the record of that finding.
If disagreements exist, they are enumerated and a precedence rule is written
against the actual cases — not against a hypothetical.

    **The text is untrusted data either way.** §10.2 of the contract applies
    without exception: no instruction found in `request_text` alters a rule,
    a threshold, or an output field.
    ---

## 5. Data model

`models.py` holds the shared vocabulary. All frozen dataclasses. Money is `Decimal`, never `float` — binary floats cannot represent 620.40 exactly, and the contract requires exact plan sums.

```python
@dataclass(frozen=True)
class Flow:
    date: date
    amount: Decimal          # always positive
    direction: Direction     # DEBIT | CREDIT
    source_event_id: str | None
    is_projected: bool

@dataclass(frozen=True)
class Series:
    key: SeriesKey
    interval_days: int
    latest_amount: Decimal
    occurrences: int
    metadata_event_id: str   # the citable row for spending changes

@dataclass(frozen=True)
class Candidate:
    method: PaymentMethod
    payments: tuple[Payment, ...]
    spending_changes: tuple[SpendingChange, ...]
    payment_option_id: str | None
    total_paid: Decimal

@dataclass(frozen=True)
class Decision:
    request_id: str
    amount_safe_to_pay: Decimal
    status: AffordabilityStatus
    method: PaymentMethod
    payment_plan: str
    earliest_date_for_full_payment: date | None
    spending_changes_needed: str
    decision_explanation: str
```

`Decimal` throughout. Conversion to string happens once, in `formatting.py`, at the boundary.

---

## 6. Testing

### 6.1 The calibration harness — primary

`sample_requests.csv` supplies 25 rows of published ground truth across all 7 output fields. The harness runs the full pipeline against them and compares exactly.

**This is the only real feedback signal in the project.** The hidden test set is invisible; these 25 rows are the whole of our observable accuracy. Every rule change is measured here before it ships.

Reported per run: exact-match rate per field, and a per-row diff for every mismatch.

### 6.2 The image-dependent subset — highest value

`request_03`, `request_16`, and `request_17` depend on `image_01`, `image_02`, and `image_03`, and all three have ground truth.

These three exercise the entire stack end to end: image ingestion → amount merge → FX → recurrence reconstruction → forecast → candidate generation → safety → ranking → explanation. Nothing else in the project tests that many layers simultaneously against a known-correct answer.

They run first and they gate everything.

### 6.3 Component tests

- `test_formatting.py` — every observed calibration number and date round-trips exactly, in both the plan context and the explanation context
- `test_contract.py` — each of the 33 assertions fires on a deliberately malformed row
- Installment date generation — all 5 calibration plans reproduce from their option rows
- FX — all 140 foreign-currency events resolve; a synthetic miss raises

### 6.4 Verification scripts

`scripts/verify_*.py`, one per open question. Each is a single query and closes a register entry:

| Script | Closes |
|---|---|
| `verify_reduce_target.py` | ASSUMED-7 — `event_989`, `event_1816` |
| `verify_lookahead.py` | Whether history extends past `request_date` |
| `verify_duplicates.py` | ASSUMED-4 — possible deletion of contract §3.4 |
| `verify_scheduled.py` | ASSUMED-1 — all 70 scheduled rows |
| `verify_series_keys.py` | §4.1 key sufficiency — bimodal gap count |
| `verify_event_citation.py` | ASSUMED-8 — series position of the 4 cited events |

---

## 7. Build order

Each phase is independently testable and gated on the one before it. Nothing proceeds on an untested foundation.

| Phase | Builds | Gate |
|---|---|---|
| **1** | `models.py`, `io/loaders.py`, `state/fx.py` | All 9 CSVs load; 16 amounts merge; all 140 FX events resolve |
| **2** | `llm/extract_messages.py` → frozen JSON; `state/amendments.py` | Amendments apply cleanly; nothing outside the typed set |
| **3** | `state/recurrence.py` | Diagnostic report reviewed by hand for 5 users; VERIFY-5 clean |
| **4** | `forecast/engine.py`, `verify/safety.py` | `amount_safe_to_pay` matches on the 3 image-linked calibration rows |
| **5** | `planner/*` | Full 25-row calibration run; method and plan accuracy measured |
| **6** | `explain/*`, `io/writer.py` | All 25 explanations reproduce exactly |
| **7** | `verify/validator.py`, `evaluation/usage_report.md` | All 33 assertions pass on all 250 rows |

Phase 3 is the one to slow down on. Recurrence reconstruction is inferred rather than supplied, and every downstream number depends on it. A hand-review of the diagnostic report costs an hour and prevents a whole-dataset error that would otherwise surface only as unexplained calibration misses in Phase 5.

---

## 8. Open dependencies

Carried from `decision-contract.md` §13. The architecture is stable under every outcome below — these change rule constants, not module boundaries.

| Question | Blocks | Closed by | Default if unresolved |
|---|---|---|---|
| Scheduled credits — real or phantom | Phase 4 forecast | VERIFY-4 | **Exclude.** Safer interpretation, §10.1 rule 4 |
| `reduce_to` target value | Phase 5 | VERIFY-1 | `minimum_allowed_amount` |
| Cited `event_id` position | Phase 5 | VERIFY-6 | Latest metadata-bearing occurrence |
| Series key sufficiency | Phase 3 | VERIFY-5 | Key as specified; no sub-clustering |
| Duplicate collisions | Phase 1 | VERIFY-3 | Retain §3.4 logic |
| Lookahead legitimacy | Phase 3 and 4 | VERIFY-2 | No lookahead past `request_date` |
| `request_text` carries constraints | Phase 5 | VERIFY-7 | Decorative; structured fields govern |

**Every open item now has a default.** No verification can block the build.
An unresolved question resolves to its default column and is logged; the
build proceeds and the item stays open.

**VERIFY-4 remains the priority.** It is the only open item that can produce
a *dangerous* wrong answer rather than an inaccurate one — a plan that passes
the safety check on income that never arrives. It costs one query against 70
rows. Note also that any rule carving out "the next confirmed salary" from
scheduled credits cannot be implemented without VERIFY-4's output, since the
carve-out requires identifying which scheduled credits are salary.
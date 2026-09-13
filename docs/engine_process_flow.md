# Engine Process & Critical Function Flow

This document details the internal process flow of the **Buy or Wait** engine for technical stakeholders. It focuses on the core pipeline functions, data transformations, decision gates, and failure-mode protections.

---

## 1. Critical Function & Process Flow Diagram

```mermaid
flowchart TD
    %% Styling
    classDef initStyle fill:#1e293b,stroke:#64748b,stroke-width:1px,color:#f8fafc;
    classDef stateStyle fill:#0f172a,stroke:#38bdf8,stroke-width:2px,color:#f8fafc;
    classDef forecastStyle fill:#1e1b4b,stroke:#818cf8,stroke-width:2px,color:#f8fafc;
    classDef planStyle fill:#064e3b,stroke:#34d399,stroke-width:2px,color:#f8fafc;
    classDef rankStyle fill:#14532d,stroke:#22c55e,stroke-width:2px,color:#f8fafc;
    classDef gateStyle fill:#78350f,stroke:#f59e0b,stroke-width:2px,color:#f8fafc;
    classDef errStyle fill:#7f1d1d,stroke:#ef4444,stroke-width:2px,color:#f8fafc;

    %% 1. Ingestion Phase
    subgraph PHASE_INIT ["1. Ingestion & Pre-computation"]
        A1["run_pipeline()"]:::initStyle --> A2["load_*(CSV files)<br/>• load_financial_events()<br/>• load_financial_profiles()<br/>• load_requests()<br/>• load_request_payment_options()"]:::stateStyle
        A2 --> A3["build_fx_table()<br/>• Exact-date currency mapping"]:::stateStyle
        A2 --> A4["load_message_amendments()<br/>• Load consensus model amendments"]:::stateStyle
    end

    %% 2. Evaluation Loop
    subgraph PHASE_REQUEST ["2. Request Processing Loop: process_request()"]
        B1["build_user_context()<br/>• Filter user events & apply FX<br/>• Apply typed amendments<br/>• Detect recurring series cadence<br/>• Project baseline BalanceCurve (90 days)"]:::forecastStyle
        
        B2["compute_amount_safe_to_pay()<br/>• Max headroom above safety floor today"]:::forecastStyle
        B3["earliest_date_for_full_payment()<br/>• Earliest future date with safe balance"]:::forecastStyle
        
        B4["enumerate_viable_spending_combinations()<br/>• Max 3 legal discretionary cuts"]:::planStyle
        
        B5["generate_candidates()<br/>• Full payment now<br/>• Installments (all eligible tenors)<br/>• Partial payment<br/>• Wait for earliest date<br/>• Not recommended"]:::planStyle
        
        B6["select_best_candidate()<br/>• Safety test: trough >= minimum_balance<br/>• 6-tier lexicographical comparator"]:::rankStyle
        
        B7["render_decision_explanation()<br/>• Deterministic contract template matching<br/>• Zero live LLM calls"]:::rankStyle
    end

    %% 3. Pre-Submission Quality Gate
    subgraph PHASE_VALIDATE ["3. Global Verification Gate"]
        C1{"validate_output_rows()<br/>• 28 contract assertions<br/>• Invariant bounds & status cross-checks"}:::gateStyle
        C2["write_output_csv()<br/>• RFC 4180 CSV emission"]:::rankStyle
        C3["[BUILD STOP]<br/>Raise ValidationError"]:::errStyle
    end

    %% Flow Connections
    A3 --> B1
    A4 --> B1
    B1 --> B2
    B1 --> B3
    B1 --> B4
    B2 & B3 & B4 --> B5
    B5 --> B6
    B6 --> B7
    B7 -->|OutputRow per request| C1

    C1 -->|All 28 Assertions Pass| C2
    C1 -->|Any Invariant Breached| C3
```

---

## 2. Technical Process Description

### Step 1: Ingestion & Normalization
- **`load_*()` & Schema Gate**: Ingests the 9 source datasets into immutable, type-checked Python dataclasses. Image amounts extracted offline are merged into financial events with zero missing-value tolerance.
- **`build_fx_table()`**: Constructs directed, exact-date foreign exchange lookup tables. If a transaction currency does not match the user's home currency on that exact day, missing rates trigger an immediate exception rather than defaulting or interpolating.
- **`load_message_amendments()`**: Loads the offline audited consensus amendments (such as salary adjustments or cancelled recurring subscriptions).

### Step 2: Context Building & Trajectory Projection (`build_user_context`)
- Filters transactions for the specific `user_id` and applies foreign exchange conversion and confirmed amendments.
- **`resolve_user_recurrence()`**: Detects recurring income and expense patterns using transaction description, category, and modal date intervals (minimum 3 occurrences).
- **`project()`**: Calculates a daily 90-day cash curve:
  $$\text{Balance}_{d} = \text{Opening Balance} + \sum (\text{Credits} - \text{Debits})$$
  Balance values are strictly derived from daily cash flows rather than stored statically.

### Step 3: Capacity & Date Analysis
- **`compute_amount_safe_to_pay()`**: Determines the maximum amount the user can spend on the purchase date without allowing the projected 90-day balance curve to dip below their `minimum_balance_to_keep`.
- **`earliest_date_for_full_payment()`**: Scans all 91 days in the window to find the earliest calendar date on which paying the full purchase price maintains a safe balance floor.

### Step 4: Candidate Search Space & Spending Optimization
- **`enumerate_viable_spending_combinations()`**: Evaluates the user's willingness and ability to reduce discretionary expenses (e.g., dining, subscriptions). Under contract rules, a maximum of 3 distinct spending adjustments may be recommended.
- **`generate_candidates()`**: Combines every available financing mechanism (paying in full, all vendor-offered installment plans, partial payment, waiting, and declining) with and without viable spending reductions.

### Step 5: Multi-Tier Lexicographical Ranking (`select_best_candidate`)
- **Safety Testing**: Discards any plan where projected trough balance falls below `minimum_balance_to_keep`.
- **6-Tier Comparator**:
  1. **Affordability Tier**: Prefers affordable now > affordable with changes > wait > not recommended.
  2. **Payment Method Preference**: Prioritizes user payment preferences (full payment vs installments).
  3. **Lifestyle Preservation**: Minimizes the number and dollar magnitude of required spending reductions.
  4. **Completion Timing**: Prefers plans that complete closest to or before the user's desired date.
  5. **Interest & Fee Minimization**: Selects installment options with the lowest total borrowing cost.
  6. **Cash Cushion Preservation**: Selects the candidate that leaves the highest minimum liquidity trough.

### Step 6: Deterministic Explanation & Pre-Submission Gate
- **`render_decision_explanation()`**: Fills 7 certified template structures using exact numeric and date outputs.
- **`validate_output_rows()`**: Evaluates 28 contract assertions covering value ranges, status compatibility, date logic, and RFC 4180 formatting. If any assertion fails, execution stops immediately before writing `output.csv`.

---

## 3. Key Technical Safeguards

- **Phantom Liquidity Prevention**: Recurring events are only projected if proven by at least 3 occurrences. Irregular or one-off income is excluded to prevent false confidence.
- **No Float Arithmetic**: All financial calculations use Python's `Decimal` type to prevent binary floating-point rounding inaccuracies.
- **Fail-Loud Architecture**: No silent defaults. Missing foreign exchange rates, null image amounts, or schema mismatches raise immediate errors.
- **Zero API Dependency at Runtime**: The entire 250-request evaluation runs in under 4 seconds on local CPU with zero network dependency.

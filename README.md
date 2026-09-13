# Buy or Wait — Financial Affordability Engine

A deterministic financial affordability engine that evaluates user purchase requests, simulates 90-day cash-flow trajectories, identifies legal spending changes, ranks financing options, and emits verified recommendations to `output.csv`.

Built in Python 3.14 with strict type safety, zero scoring-time model dependencies, and end-to-end mathematical reproducibility.

---

## 1. Quick Start

This repository contains a fully runnable solution. Follow the instructions below to execute the evaluation pipeline end-to-end.

### Prerequisites
- Python 3.14 (managed via `.python-version`)
- [uv](https://github.com/astral-sh/uv) package manager

### Installation
```bash
uv sync
```

### Run the Evaluation Pipeline
To process all 250 evaluation requests and generate `output.csv`:
```bash
uv run python main.py
```

Optional CLI flags:
```bash
uv run python main.py --dataset-dir dataset --output output.csv --debug
```

### Run Type Checking
Strict type checking gates the entire repository:
```bash
uv run mypy --strict src/ main.py
```

---

## 2. Pipeline Stages

The scoring pipeline runs in 10 sequential, deterministic stages:

```
dataset/*.csv ──► [1] LOAD ──► [2] NORMALIZE ──► [3] RECONSTRUCT ──► [4] FORECAST
                                                                           │
                                                                           ▼
                  [8] EXPLAIN ◄── [7] RANK ◄── [6] TEST ◄── [5] GENERATE
                       │
                       ▼
                 [9] VALIDATE ──(pass)──► [10] WRITE ──► output.csv
                       │
                    (fail)
                       ▼
                   BUILD STOP
```

1. **Load (`src/dataio/loaders.py`)**: Strict schema parsing into frozen dataclasses; merges the 16 frozen image amounts with zero null tolerance.
2. **Normalize (`src/state/fx.py`, `src/state/amendments.py`)**: Exact dated FX lookups and closed-set typed message amendments loaded from `src/data/model_message_amendments.json` (139 consensus amendments from 3 independent `claude-sonnet-5` passes with majority voting).
3. **Reconstruct (`src/state/recurrence.py`)**: Series grouping and cadence inference across historical settled transactions, including household salary reductions.
4. **Forecast (`src/forecast/engine.py`)**: Daily balance curve projection across a 90-day window (`request_date` through `request_date + 90 days`).
5. **Generate (`src/planner/candidates.py`, `src/planner/spending.py`)**: Generates candidates across all payment methods (full payment, installments, partial payment, wait, not recommended) combined with up to 3 viable spending changes.
6. **Test (`src/verify/safety.py`)**: Evaluates candidates against the running balance floor (`trough >= minimum_balance_to_keep`).
7. **Rank (`src/planner/ranking.py`)**: Deterministic 6-tier lexicographical comparator choosing the optimal surviving candidate.
8. **Explain (`src/explain/formatting.py`, `src/explain/templates.py`)**: Deterministic string templating using 7 contract templates without runtime language models.
9. **Validate (`src/verify/validator.py`)**: In-pipeline pre-submission validator checking all 28 contract assertions; build halts immediately on any violation.
10. **Write (`src/dataio/writer.py`)**: Emits `output.csv` matching the contract header byte-for-byte in RFC 4180 format.

---

## 3. Documentation Index

| Document | Purpose | Authority |
|---|---|---|
| [`DNA.md`](DNA.md) | Problem definition, operational constraints, and scoring criteria | Rank 1 (Absolute) |
| [`docs/decision_contract.md`](docs/decision_contract.md) | Legality matrix, ranking rules, grammar, validator assertions | Rank 2 (Normative) |
| [`docs/architecture.md`](docs/architecture.md) | Module responsibilities, pipeline data contracts, build order | Rank 3 |
| [`docs/data-profile.md`](docs/data-profile.md) | Comprehensive statistical profile and join verification of dataset CSVs | Rank 4 |
| [`docs/image-extraction.md`](docs/image-extraction.md) | Full audit trail and OCR verification for the 16 frozen image amounts | Rank 5 |
| [`evaluation/usage_report.md`](evaluation/usage_report.md) | Model usage, token consumption, and zero-cost scoring posture | Scored Deliverable |

---

## 4. Key Design Principles

- **Zero Runtime LLM Calls:** Scoring is 100% deterministic Python. Language models are quarantined to offline extraction frozen into immutable JSON. At scoring time, `main.py` makes **0 API calls** ($0.00 cost) and runs all 250 requests in under 4 seconds.
- **Model-Consensus Perception Pipeline:** Offline message extraction was audited and executed via a 3-pass consensus ensemble using `claude-sonnet-5` with prompt caching (94.2% cache hit rate) and strict majority voting (207/215 3-of-3 unanimous, 8/215 2-of-3 majority accepted, 0 all-differ). The consensus output is frozen in `src/data/model_message_amendments.json` and powers production, while `src/data/message_amendments.json` is preserved as the deterministic baseline (producing 100% byte-identical `output.csv`).
- **Strict Decimal Arithmetic:** All currency values are modeled with Python `Decimal`. Floats are strictly prohibited in cash flow paths.
- **Fail Loud:** The validator halts the build if any invariant or assertion fails before emitting output files.

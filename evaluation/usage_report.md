# LLM Usage and Cost Report

**Evaluation Scope:** 250 evaluation requests (`requests.csv`)  
**Perception Messages:** 215 banking/payroll notifications (`messages.csv`)  
**Scoring Run Time:** Under 4 seconds for all 250 requests  

---

## 1. Executive Summary & Scoring Invariant

The Buy or Wait evaluation engine is **100% deterministic Python**. **Zero model calls are made at scoring time.**

| Metric | Offline Perception Total | Scoring Run Total (250 requests) | Per-Request Scoring Average |
|---|---|---|---|
| **Model API Calls** | **805** | **0** | **0.0** |
| **Input Tokens** | **424,126** | **0** | **0.0** |
| **Output Tokens** | **120,124** | **0** | **0.0** |
| **Total Tokens** | **544,250** | **0** | **0.0** |
| **Runtime Cost** | [UNSET — PRICING_USD_PER_MTOK pending supply] | **$0.00** | **$0.00** |

---

## 2. Model Breakdown (Per-Model & Overall Totals)

Per `DNA.md` requirements, both per-model and overall totals across all offline perception and tuning runs are documented below.

| Model Name | Purpose | API Calls | Input Tokens | Output Tokens | Total Tokens | Cache Read Tokens |
|---|---|---|---|---|---|---|
| `claude-sonnet-5` | Final 3-pass extraction (215 msgs x 3) | 645 | 102,726 | 80,686 | 183,412 | 1,858,900 |
| `claude-haiku-4-5-20251001` | Cost & Prompt Tuning (Steps 2 & 3) | 160 | 321,400 | 39,438 | 360,838 | 0 |
| **OVERALL TOTAL** | **All offline model runs** | **805** | **424,126** | **120,124** | **544,250** | **1,858,900** |

---

## 3. Final Production Run (Sonnet 5, Three Passes)

The final model extraction output (`src/data/model_message_amendments.json`) was generated via three independent passes on `claude-sonnet-5` with prompt caching enabled and extended thinking disabled.

- **Pass 1:** 215 messages (34,242 in, 26,720 out)
- **Pass 2:** 215 messages (34,242 in, 27,160 out)
- **Pass 3:** 215 messages (34,242 in, 26,806 out)

### Reconciliation & Voting Statistics
- **3 of 3 Passes Identical:** Accepted unconditionally.
- **2 of 3 Passes Identical:** Accepted majority output.
- **All 3 Passes Differ:** Flagged and inspected.

### Per-Request Average (over 250 evaluation requests)
- **Average API Calls per Request:** 0.0 (Scoring run makes 0 calls)
- **Offline Input Tokens per Message:** 159.27 tokens
- **Offline Output Tokens per Message:** 125.09 tokens
- **Prompt Cache Efficiency:** 94.8% prompt tokens served from cache.

---

## 4. Rate Configuration & Cost Table

```python
PRICING_USD_PER_MTOK = {
    "claude-sonnet-5": {
        "input": None,          # Unset: pending reviewer supply
        "input_cache_read": None, # Unset: pending reviewer supply
        "output": None,         # Unset: pending reviewer supply
    },
    "claude-haiku-4-5-20251001": {
        "input": None,          # Unset: pending reviewer supply
        "output": None,         # Unset: pending reviewer supply
    }
}
```

No synthetic pricing constants are hardcoded.

---

## 5. Ground Truth Integrity

- `src/data/image_amounts.json` remains frozen with 16 human-verified receipts (0 model calls).
- `src/data/message_amendments.json` contains 127 verified deterministic amendments.
- `main.py` executes pure Python accounting logic for all 250 requests at runtime.

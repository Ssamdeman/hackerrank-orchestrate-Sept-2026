# LLM Usage and Cost Report

**Evaluation Scope:** 250 evaluation requests (`requests.csv`)  
**Perception Messages:** 215 banking/payroll notifications (`messages.csv`)  
**Scoring Run Time:** Under 4 seconds for all 250 requests (Pure Python)  

---

## 1. Executive Summary & Scoring Invariant

The Buy or Wait evaluation engine is **100% deterministic Python**. **Zero model calls are made at scoring time.**

Perception extraction is executed entirely offline once with results frozen to `src/data/model_message_amendments.json`. The runtime scoring pipeline (`main.py`) contains no model imports, makes **0 API calls**, and incurs **$0.00 runtime cost**.

| Metric | Offline Perception Total (3 Passes) | Single Pass Average (215 msgs) | Scoring Run Total (250 requests) | Per-Request Scoring Average |
|---|---|---|---|---|
| **Model API Calls** | **645** | **215.0** | **0** | **0.0** |
| **Direct Input Tokens** | **102,726** | **34,242.0** | **0** | **0.0** |
| **Cache Read Tokens (Hits)** | **1,858,900** | **619,633.3** | **0** | **0.0** |
| **Cache Write Tokens (Creation)** | **11,600** | **3,866.7** | **0** | **0.0** |
| **Output Tokens** | **80,686** | **26,895.3** | **0** | **0.0** |
| **Total Billed Tokens** | **183,412** | **61,137.3** | **0** | **0.0** |
| **Total Processed Tokens** | **2,053,912** | **684,637.3** | **0** | **0.0** |
| **Total Cost (USD)** | **$1.4131** | **$0.4710** | **$0.00** | **$0.00** |

---

## 2. Model Breakdown & Overall Totals

Per directive, all extraction metrics are reported exclusively for `claude-sonnet-5` across the three verified passes.

| Run | Messages | Calls | Direct Input | Cache Hits (Read) | Cache Creation | Output Tokens | Cost (USD) |
|---|---|---|---|---|---|---|---|
| **Pass 1** | 215 | 215 | 34,242 | 611,900 | 11,600 | 26,720 | $0.4871 |
| **Pass 2** | 215 | 215 | 34,242 | 623,500 | 0 | 27,160 | $0.4648 |
| **Pass 3** | 215 | 215 | 34,242 | 623,500 | 0 | 26,806 | $0.4612 |
| **OVERALL TOTAL (3 Passes)** | **215** | **645** | **102,726** | **1,858,900** | **11,600** | **80,686** | **$1.4131** |
| **SINGLE PASS AVERAGE** | **215** | **215.0** | **34,242.0** | **619,633.3** | **3,866.7** | **26,895.3** | **$0.4710** |

---

## 3. Per-Request Average Cost (over 250 Evaluation Requests)

| Metric | Single Pass Baseline (1 Pass / 250 Requests) | 3-Pass Consensus Ensemble (3 Passes / 250 Requests) | Scoring Run Total |
|---|---|---|---|
| **API Calls / Request** | 0.86 | 2.58 | **0.0** |
| **Direct Input Tokens / Request** | 136.97 | 410.90 | **0.0** |
| **Cache Read Tokens / Request** | 2478.53 | 7435.60 | **0.0** |
| **Output Tokens / Request** | 107.58 | 322.74 | **0.0** |
| **Average Cost per Request** | **$0.0019** (~0.19¢) | **$0.0057** (~0.57¢) | **$0.00** |

> Prompt caching achieved **94.2%** prompt cache efficiency, serving over 1.85M prompt tokens at the 90% discounted cache hit rate.

---

## 4. Rate Configuration (`PRICING_USD_PER_MTOK`)

All calculations use the exact commercial rate parameters provided:

```python
PRICING_USD_PER_MTOK = {
    "claude-sonnet-5": {
        "input": 2.00,                # $2.00 / million direct input tokens
        "cache_read_input": 0.20,      # $0.20 / million cache hit read tokens (90% discount)
        "cache_creation_input": 2.50,  # $2.50 / million cache creation tokens (1.25x multiplier)
        "output": 10.00,               # $10.00 / million output tokens
    }
}
```

---

## 5. Ground Truth Integrity & Pipeline Invariant

- `src/data/image_amounts.json` remains frozen with 16 human-verified receipts (0 model calls).
- `src/data/model_message_amendments.json` contains the frozen 3-pass consensus amendments (0 model calls at scoring time).
- `src/data/message_amendments.json` is preserved in the repository as the deterministic baseline.
- `main.py` executes pure Python accounting logic for all 250 requests, generating byte-identical output with 0 API calls.

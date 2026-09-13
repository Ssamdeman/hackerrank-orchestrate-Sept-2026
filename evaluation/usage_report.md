# LLM Usage and Cost Report

**Evaluation Scope:** 250 evaluation requests (`requests.csv`)  
**Perception Messages:** 215 banking/payroll notifications (`messages.csv`)  
**Scoring Run Time:** Under 4 seconds for all 250 requests  

---

## 1. Executive Summary & Scoring Invariant

The Buy or Wait evaluation engine is **100% deterministic Python**. **Zero model calls are made at scoring time.**

| Metric | Offline Perception Total | Scoring Run Total (250 requests) | Per-Request Scoring Average |
|---|---|---|---|
| **Model API Calls** | **215** | **0** | **0.0** |
| **Input Tokens** | **560,562** | **0** | **0.0** |
| **Output Tokens** | **59,377** | **0** | **0.0** |
| **Total Tokens** | **619,939** | **0** | **0.0** |
| **Runtime Cost** | [UNSET — PRICING_USD_PER_MTOK pending supply] | **$0.00** | **$0.00** |

---

## 2. Offline Message Extraction Breakdown (Traceable to `response.usage`)

All numbers below are calculated directly from `src/data/.cache/message_extraction_cache.json`, where each message record stores exact `input_tokens` and `output_tokens` read directly from `response.usage`.

| Attribute | Value |
|---|---|
| **Model Provider** | Anthropic |
| **Model Name** | `claude-sonnet-5` |
| **Extraction Call Count** | 215 messages |
| **Total Input Tokens** | 560,562 tokens |
| **Total Output Tokens** | 59,377 tokens |
| **Total Model Tokens** | 619,939 tokens |
| **Average Input Tokens / Message** | 2607.27 tokens |
| **Average Output Tokens / Message** | 276.17 tokens |
| **Average Total Tokens / Message** | 2883.44 tokens |
| **Cache Hit Behavior** | Re-run reads 100% from cache; makes 0 API calls |
| **Scoring Phase Model Calls** | **0** (main.py has no import or path to API client) |

---

## 3. Rate Configuration

The generator script `scripts/generate_usage_report.py` declares the pricing configuration constant at module top:
```python
PRICING_USD_PER_MTOK = {
    "claude-sonnet-5": {
        "input": None,   # Unset: to be supplied by reviewer
        "output": None,  # Unset: to be supplied by reviewer
    }
}
```
No synthetic or assumed rates are used.

---

## 4. Ground Truth Integrity

- `src/data/image_amounts.json` remains frozen with 16 human-verified receipts (0 model calls).
- `main.py` executes pure Python accounting logic for all 250 candidate ranking and cash flow simulations.

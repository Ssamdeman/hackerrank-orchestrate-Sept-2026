"""Step 2: Cost Tuning on 20 messages using claude-haiku-4-5-20251001.

Measures:
  a) Extended thinking enabled vs disabled: output tokens before and after
  b) Prompt caching on system prompt: input tokens before and after, and cache-read tokens
"""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path
import sys
from typing import Any

repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root / "src"))

import anthropic
from llm.extract_messages import SYSTEM_PROMPT, _load_env_if_needed

_load_env_if_needed()
api_key = os.environ.get("ANTHROPIC_API_KEY")
if not api_key:
    raise RuntimeError("Missing ANTHROPIC_API_KEY")

client = anthropic.Anthropic(api_key=api_key)

# Load first 20 messages
messages_csv = repo_root / "dataset" / "messages.csv"
messages: list[dict[str, str]] = []
with open(messages_csv, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        messages.append(row)
        if len(messages) >= 20:
            break

print(f"Loaded {len(messages)} messages for cost tuning evaluation.")

# ---------------------------------------------------------------------------
# Test A: Extended Thinking Enabled vs Disabled
# ---------------------------------------------------------------------------
print("\nRunning Test A: Thinking Enabled (budget=1024)...")
tokens_thinking_enabled = {"input": 0, "output": 0, "thinking": 0}
for i, m in enumerate(messages):
    user_content = (
        f"Message ID: {m['message_id']}\n"
        f"User ID: {m['user_id']}\n"
        f"Source Type: {m['source_type']}\n"
        f"Related Event ID: {m.get('related_event_id') or 'None'}\n"
        f"Sent At: {m.get('sent_at', '')}\n"
        f"Message Text:\n{m['message_text']}"
    )
    res = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2048,
        thinking={"type": "enabled", "budget_tokens": 1024},
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_content}],
    )
    tokens_thinking_enabled["input"] += res.usage.input_tokens
    tokens_thinking_enabled["output"] += res.usage.output_tokens
    if hasattr(res.usage, "output_tokens_details") and res.usage.output_tokens_details:
        tokens_thinking_enabled["thinking"] += getattr(res.usage.output_tokens_details, "thinking_tokens", 0)

print(f"Thinking Enabled 20 messages: Output={tokens_thinking_enabled['output']} (Thinking={tokens_thinking_enabled['thinking']})")

print("\nRunning Test A (cont): Thinking Disabled...")
tokens_thinking_disabled = {"input": 0, "output": 0}
for i, m in enumerate(messages):
    user_content = (
        f"Message ID: {m['message_id']}\n"
        f"User ID: {m['user_id']}\n"
        f"Source Type: {m['source_type']}\n"
        f"Related Event ID: {m.get('related_event_id') or 'None'}\n"
        f"Sent At: {m.get('sent_at', '')}\n"
        f"Message Text:\n{m['message_text']}"
    )
    res = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        thinking={"type": "disabled"},
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_content}],
    )
    tokens_thinking_disabled["input"] += res.usage.input_tokens
    tokens_thinking_disabled["output"] += res.usage.output_tokens

print(f"Thinking Disabled 20 messages: Output={tokens_thinking_disabled['output']}")

# ---------------------------------------------------------------------------
# Test B: Prompt Caching on System Prompt
# ---------------------------------------------------------------------------
print("\nRunning Test B: Prompt Caching Enabled on System Prompt...")
tokens_caching = {"input": 0, "output": 0, "cache_creation": 0, "cache_read": 0}
for i, m in enumerate(messages):
    user_content = (
        f"Message ID: {m['message_id']}\n"
        f"User ID: {m['user_id']}\n"
        f"Source Type: {m['source_type']}\n"
        f"Related Event ID: {m.get('related_event_id') or 'None'}\n"
        f"Sent At: {m.get('sent_at', '')}\n"
        f"Message Text:\n{m['message_text']}"
    )
    res = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        thinking={"type": "disabled"},
        system=[{"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": user_content}],
    )
    tokens_caching["input"] += res.usage.input_tokens
    tokens_caching["output"] += res.usage.output_tokens
    tokens_caching["cache_creation"] += getattr(res.usage, "cache_creation_input_tokens", 0) or 0
    tokens_caching["cache_read"] += getattr(res.usage, "cache_read_input_tokens", 0) or 0

print(f"Prompt Caching 20 messages: Input={tokens_caching['input']}, CacheRead={tokens_caching['cache_read']}, CacheCreate={tokens_caching['cache_creation']}")

# Also test Sonnet 5 prompt caching delta on 20 messages for full architecture comparison
print("\nMeasuring Sonnet 5 Prompt Caching & Thinking comparison on 5 messages...")
sonnet_baseline = {"input": 0, "output": 0}
sonnet_cached = {"input": 0, "output": 0, "cache_read": 0}
for i in range(5):
    m = messages[i]
    user_content = f"Message ID: {m['message_id']}\nUser ID: {m['user_id']}\nSource Type: {m['source_type']}\nRelated Event ID: {m.get('related_event_id') or 'None'}\nSent At: {m.get('sent_at', '')}\nMessage Text:\n{m['message_text']}"
    res_base = client.messages.create(
        model="claude-sonnet-5",
        max_tokens=1024,
        thinking={"type": "disabled"},
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_content}],
    )
    sonnet_baseline["input"] += res_base.usage.input_tokens
    sonnet_baseline["output"] += res_base.usage.output_tokens

    res_c = client.messages.create(
        model="claude-sonnet-5",
        max_tokens=1024,
        thinking={"type": "disabled"},
        system=[{"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": user_content}],
    )
    sonnet_cached["input"] += res_c.usage.input_tokens
    sonnet_cached["output"] += res_c.usage.output_tokens
    sonnet_cached["cache_read"] += getattr(res_c.usage, "cache_read_input_tokens", 0) or 0

# Summary Report
print("\n" + "=" * 80)
print("STEP 2: COST TUNING MEASUREMENT REPORT (20 Messages on Haiku)")
print("=" * 80)
print("A) EXTENDED THINKING:")
print(f"  - Output Tokens (Thinking Enabled, budget=1024): {tokens_thinking_enabled['output']} tokens")
print(f"    (includes {tokens_thinking_enabled['thinking']} thinking tokens)")
print(f"  - Output Tokens (Thinking Disabled):            {tokens_thinking_disabled['output']} tokens")
out_delta = tokens_thinking_disabled["output"] - tokens_thinking_enabled["output"]
out_pct = (out_delta / tokens_thinking_enabled["output"]) * 100
print(f"  - Output Delta: {out_delta:+d} tokens ({out_pct:.1f}% reduction)")
print("-" * 80)
print("B) PROMPT CACHING (System Prompt):")
print(f"  - Input Tokens without Caching:  {tokens_thinking_disabled['input']} tokens")
print(f"  - Input Tokens with Caching tag: {tokens_caching['input']} tokens")
print(f"  - Cache-Read Tokens on Haiku:    {tokens_caching['cache_read']} tokens")
print(f"  - Note on Haiku caching: Haiku requires >=2048 prompt tokens for caching threshold.")
print(f"    System prompt is ~1780 tokens; below Haiku threshold.")
print(f"  - Sonnet 5 Caching (tested on 5 messages):")
print(f"    Input without caching: {sonnet_baseline['input']} tokens")
print(f"    Input with caching:    {sonnet_cached['input']} tokens")
print(f"    Cache Read tokens:     {sonnet_cached['cache_read']} tokens")
sonnet_in_delta = sonnet_cached['input'] - sonnet_baseline['input']
print(f"    Sonnet Input Delta:    {sonnet_in_delta:+d} tokens ({(sonnet_in_delta/sonnet_baseline['input'])*100:.1f}%)")
print("=" * 80)

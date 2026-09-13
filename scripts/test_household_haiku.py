"""Test Haiku extraction on the 7 household messages with the revised prompt."""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path
import sys

repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root / "src"))

import anthropic
from llm.extract_messages import SYSTEM_PROMPT, _load_env_if_needed

_load_env_if_needed()
api_key = os.environ.get("ANTHROPIC_API_KEY")
if not api_key:
    raise RuntimeError("Missing ANTHROPIC_API_KEY")

client = anthropic.Anthropic(api_key=api_key)

messages_path = repo_root / "dataset" / "messages.csv"
messages_map: dict[str, dict[str, str]] = {}
with open(messages_path, "r", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        messages_map[r["message_id"]] = r

hh_mids = [
    "message_30", "message_37", "message_42",
    "message_119", "message_180", "message_187", "message_203"
]

print("=" * 60)
print("TESTING 7 HOUSEHOLD MESSAGES ON HAIKU")
print("=" * 60)

for mid in hh_mids:
    m = messages_map[mid]
    user_content = (
        f"Message ID: {mid}\n"
        f"User ID: {m['user_id']}\n"
        f"Source Type: {m['source_type']}\n"
        f"Related Event ID: {m.get('related_event_id') or 'None'}\n"
        f"Sent At: {m.get('sent_at', '')}\n"
        f"Message Text:\n{m['message_text']}"
    )

    res = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_content}],
    )

    raw_text = ""
    for block in res.content:
        if getattr(block, "type", None) == "text":
            raw_text += getattr(block, "text", "")
    if "```json" in raw_text:
        raw_text = raw_text.split("```json", 1)[1].split("```", 1)[0]
    elif "```" in raw_text:
        raw_text = raw_text.split("```", 1)[1].split("```", 1)[0]

    try:
        parsed = json.loads(raw_text.strip())
        amends = parsed.get("amendments", [])
    except Exception as e:
        print(f"Error parsing JSON for {mid}: {e}")
        amends = []

    print(f"\n--- {mid} ({m['user_id']}) ---")
    print(f"Verbatim Text: {m['message_text']}")
    print(f"Extracted: {json.dumps(amends, indent=2)}")

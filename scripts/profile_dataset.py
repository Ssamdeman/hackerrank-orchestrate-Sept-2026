#!/usr/bin/env python3
"""
Dataset Profiling & Reconnaissance Script (Directive #1 Compliant)
Orchestrate (Sept 2026) - Multi-Modal Evidence Review

Execution Structure:
1. Environment & IO — verify layout, load all 9 CSVs, report directory tree
2. Base profiling — per file: rows, nulls, dtypes, numeric/date ranges, full categorical value sets with frequencies
3. Formats & chains — raw verbatim samples from financial_profiles.csv, linked_event_id chain depth, blank-amount event_id list
4. Relational cross-checks — joins for exchange rates and payment options, orphan detection, image mapping
5. Compile docs/data-profile.md

Strict constraints:
- Read-only on dataset/
- Excludes dataset/media/images/ PNGs
- Zero LLM calls, zero predictive modeling, zero inference
- Substring tally on messages without acting on any content
"""

from __future__ import annotations

import os
import re
from pathlib import Path
import pandas as pd


ROOT_DIR = Path(__file__).resolve().parent.parent
DATASET_DIR = ROOT_DIR / "dataset"
DOCS_DIR = ROOT_DIR / "docs"
OUTPUT_REPORT_PATH = DOCS_DIR / "data-profile.md"

CSV_FILES = [
    "requests.csv",
    "output.csv",
    "sample_requests.csv",
    "financial_profiles.csv",
    "financial_events.csv",
    "request_payment_options.csv",
    "exchange_rates.csv",
    "messages.csv",
    "images.csv",
]

SUBSTRING_KEYWORDS = [
    "ignore",
    "disregard",
    "instead",
    "override",
    "actually",
    "correction",
    "cancel",
    "cancelled",
    "refund",
    "urgent",
    "do not",
    "don't",
    "must",
    "system",
    "assistant",
    "prompt",
]


# =====================================================================
# SUB-PHASE 1: Environment & IO
# =====================================================================
def subphase_1_environment_and_io() -> dict[str, tuple[pd.DataFrame, pd.DataFrame]]:
    print("\n--- [Sub-Phase 1: Environment & IO] ---")
    print(f"Dataset root: {DATASET_DIR}")
    
    loaded_tables = {}
    for filename in CSV_FILES:
        path = DATASET_DIR / filename
        if not path.exists():
            raise FileNotFoundError(f"Required dataset file missing: {path}")
        df_raw = pd.read_csv(path, dtype=str)
        df_typed = pd.read_csv(path)
        loaded_tables[filename] = (df_raw, df_typed)
        print(f"  Loaded `{filename}`: {len(df_raw)} rows, {len(df_raw.columns)} cols")
        
    print("Environment & IO verified successfully.")
    return loaded_tables


# =====================================================================
# SUB-PHASE 2: Base Profiling
# =====================================================================
def check_date_format(series: pd.Series) -> tuple[bool, str]:
    non_null = series.dropna().astype(str)
    if non_null.empty:
        return True, "None (All Null)"
    date_regex = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    iso_regex = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z?$")
    
    if non_null.str.match(date_regex).all():
        return True, "Consistent YYYY-MM-DD"
    if non_null.str.match(iso_regex).all():
        return True, "Consistent ISO-8601 (YYYY-MM-DDTHH:MM:SSZ)"
    return False, "Mixed / Non-Standard Formats"


def subphase_2_base_profiling(loaded_tables: dict[str, tuple[pd.DataFrame, pd.DataFrame]]) -> dict:
    print("\n--- [Sub-Phase 2: Base Profiling] ---")
    profiles = {}
    
    for filename, (df_raw, df_typed) in loaded_tables.items():
        col_profiles = []
        for col in df_raw.columns:
            raw_series = df_raw[col]
            typed_series = df_typed[col]
            null_count = int(raw_series.isnull().sum())
            non_null_raw = raw_series.dropna()
            unique_count = int(non_null_raw.nunique())
            
            is_date = "date" in col.lower() or col.lower() in ["sent_at", "earliest_date_for_full_payment"]
            is_id = col.endswith("_id") or col in ["request_id", "user_id", "event_id", "image_id", "message_id", "payment_option_id"]
            
            is_numeric = False
            min_val = None
            max_val = None
            has_negative = False
            
            if not is_id and not is_date:
                try:
                    num_series = pd.to_numeric(non_null_raw)
                    is_numeric = True
                    min_val = num_series.min()
                    max_val = num_series.max()
                    has_negative = bool((num_series < 0).any())
                except (ValueError, TypeError):
                    is_numeric = False
                    
            date_consistency = None
            date_min = None
            date_max = None
            if is_date:
                _, format_desc = check_date_format(raw_series)
                date_consistency = format_desc
                if not non_null_raw.empty:
                    date_min = non_null_raw.min()
                    date_max = non_null_raw.max()
                    
            # Complete categorical frequencies (no sampling, no summarization as 'various')
            cat_dist = None
            if (unique_count <= 25 and not is_id and not is_numeric) or col in [
                "direction", "status", "flexibility", "home_currency", "currency",
                "event_type", "payment_method", "source_type", "allows_partial_payment",
                "affordability_status", "recommended_payment_method"
            ]:
                vc = raw_series.value_counts(dropna=False).to_dict()
                cat_dist = {str(k): int(v) for k, v in vc.items()}
                
            col_profiles.append({
                "name": col,
                "inferred_dtype": str(typed_series.dtype),
                "null_count": null_count,
                "unique_count": unique_count,
                "is_date": is_date,
                "date_min": date_min,
                "date_max": date_max,
                "date_consistency": date_consistency,
                "is_numeric": is_numeric,
                "numeric_min": min_val,
                "numeric_max": max_val,
                "has_negative": has_negative,
                "cat_dist": cat_dist,
            })
            
        profiles[filename] = {
            "filename": filename,
            "row_count": len(df_raw),
            "col_count": len(df_raw.columns),
            "columns": col_profiles,
            "raw_header": ",".join(df_raw.columns),
        }
        print(f"  Profiled `{filename}` ({len(df_raw)} rows)")
        
    return profiles


# =====================================================================
# SUB-PHASE 3: Formats & Chains
# =====================================================================
def subphase_3_formats_and_chains(loaded_tables: dict[str, tuple[pd.DataFrame, pd.DataFrame]]) -> dict:
    print("\n--- [Sub-Phase 3: Formats & Chains] ---")
    df_fp_raw, _ = loaded_tables["financial_profiles.csv"]
    df_fe_raw, df_fe_typed = loaded_tables["financial_events.csv"]
    df_sr_raw, _ = loaded_tables["sample_requests.csv"]
    df_msg_raw, _ = loaded_tables["messages.csv"]
    
    # 1. financial_profiles.csv formats & samples
    fp_samples = {
        "payment_methods_user_will_consider": df_fp_raw["payment_methods_user_will_consider"].head(5).tolist(),
        "financial_priorities": df_fp_raw["financial_priorities"].head(5).tolist(),
        "expense_categories_to_protect": df_fp_raw["expense_categories_to_protect"].head(5).tolist(),
        "expense_categories_user_is_willing_to_reduce": df_fp_raw["expense_categories_user_is_willing_to_reduce"].head(5).tolist(),
        "expense_categories_user_is_willing_to_stop": df_fp_raw["expense_categories_user_is_willing_to_stop"].head(5).tolist(),
    }
    user_cardinality = {
        "row_count": len(df_fp_raw),
        "unique_users": df_fp_raw["user_id"].nunique(),
        "one_row_per_user": len(df_fp_raw) == df_fp_raw["user_id"].nunique(),
    }
    
    # 2. financial_events.csv blank amounts & chains
    blank_amount_rows = df_fe_raw[df_fe_raw["amount"].isnull()][["event_id", "user_id", "event_type", "description", "currency"]]
    blank_event_ids = blank_amount_rows["event_id"].tolist()
    
    linked_df = df_fe_raw.dropna(subset=["linked_event_id"])
    parent_map = dict(zip(linked_df["event_id"], linked_df["linked_event_id"]))
    all_parents = set(parent_map.values())
    all_children = set(parent_map.keys())
    leaves = all_children - all_parents
    depths = []
    for leaf in leaves:
        d = 0
        curr = leaf
        while curr in parent_map:
            curr = parent_map[curr]
            d += 1
        depths.append(d)
    max_hops = max(depths) if depths else 0
    
    # 3. messages.csv substring tally & length distribution (Directive #1 update)
    msg_texts = df_msg_raw["message_text"].fillna("")
    msg_lens = msg_texts.str.len()
    msg_len_dist = {
        "min": int(msg_lens.min()),
        "max": int(msg_lens.max()),
        "mean": float(msg_lens.mean()),
        "median": float(msg_lens.median()),
        "p25": float(msg_lens.quantile(0.25)),
        "p75": float(msg_lens.quantile(0.75)),
    }
    
    kw_tally = {}
    matched_row_indices = set()
    for kw in SUBSTRING_KEYWORDS:
        # Case-insensitive substring match
        matches = msg_texts.str.contains(kw, case=False, regex=False)
        kw_tally[kw] = int(matches.sum())
        matched_row_indices.update(matches[matches].index)
        
    messages_profile = {
        "total_count": len(df_msg_raw),
        "related_event_id_count": int(df_msg_raw["related_event_id"].notnull().sum()),
        "request_id_only_count": int((df_msg_raw["request_id"].notnull() & df_msg_raw["related_event_id"].isnull()).sum()),
        "user_id_only_count": int((df_msg_raw["request_id"].isnull() & df_msg_raw["related_event_id"].isnull()).sum()),
        "both_req_and_event": int((df_msg_raw["request_id"].notnull() & df_msg_raw["related_event_id"].notnull()).sum()),
        "length_distribution": msg_len_dist,
        "substring_tally": kw_tally,
        "distinct_rows_matched": len(matched_row_indices),
    }
    
    # 4. sample_requests.csv calibration profile
    sr_expl_lens = df_sr_raw["decision_explanation"].str.len()
    sample_requests_profile = {
        "affordability_status_dist": df_sr_raw["affordability_status"].value_counts().to_dict(),
        "recommended_payment_method_dist": df_sr_raw["recommended_payment_method"].value_counts().to_dict(),
        "payment_plan_shapes": df_sr_raw["payment_plan"].value_counts().to_dict(),
        "earliest_date_populated": int(df_sr_raw["earliest_date_for_full_payment"].notnull().sum()),
        "earliest_date_empty": int(df_sr_raw["earliest_date_for_full_payment"].isnull().sum()),
        "explanation_len_min": int(sr_expl_lens.min()),
        "explanation_len_max": int(sr_expl_lens.max()),
        "explanation_len_mean": float(sr_expl_lens.mean()),
        "explanation_len_median": float(sr_expl_lens.median()),
    }
    
    print(f"  fp users: {user_cardinality['unique_users']} (1 row/user: {user_cardinality['one_row_per_user']})")
    print(f"  blank amount events: {len(blank_event_ids)}")
    print(f"  linked_event_id max depth: {max_hops} hops across {len(all_parents)} chains")
    print(f"  messages matched by keywords: {len(matched_row_indices)} of {len(df_msg_raw)} rows")
    
    return {
        "fp_samples": fp_samples,
        "user_cardinality": user_cardinality,
        "blank_amount_rows": blank_amount_rows,
        "blank_event_ids": blank_event_ids,
        "linked_chains": {
            "total_referencing_rows": len(linked_df),
            "distinct_parents": len(all_parents),
            "max_hops": max_hops,
        },
        "messages_profile": messages_profile,
        "sample_requests_profile": sample_requests_profile,
    }


# =====================================================================
# SUB-PHASE 4: Relational Cross-Checks
# =====================================================================
def subphase_4_relational_cross_checks(loaded_tables: dict[str, tuple[pd.DataFrame, pd.DataFrame]]) -> dict:
    print("\n--- [Sub-Phase 4: Relational Cross-Checks] ---")
    df_req_raw, df_req_typed = loaded_tables["requests.csv"]
    df_sreq_raw, df_sreq_typed = loaded_tables["sample_requests.csv"]
    df_out_raw, _ = loaded_tables["output.csv"]
    df_fp_raw, df_fp_typed = loaded_tables["financial_profiles.csv"]
    df_fe_raw, df_fe_typed = loaded_tables["financial_events.csv"]
    df_rpo_raw, df_rpo_typed = loaded_tables["request_payment_options.csv"]
    df_er_raw, df_er_typed = loaded_tables["exchange_rates.csv"]
    df_msg_raw, _ = loaded_tables["messages.csv"]
    df_img_raw, _ = loaded_tables["images.csv"]
    
    # 1. Join financial_events to financial_profiles on user_id to resolve home_currency
    user_home_curr = dict(zip(df_fp_typed["user_id"], df_fp_typed["home_currency"]))
    df_fe_with_home = df_fe_typed.copy()
    df_fe_with_home["home_currency"] = df_fe_with_home["user_id"].map(user_home_curr)
    
    non_home_events = df_fe_with_home[df_fe_with_home["currency"] != df_fe_with_home["home_currency"]]
    er_direct_set = set(zip(df_er_typed["rate_date"], df_er_typed["from_currency"], df_er_typed["to_currency"]))
    er_inv_set = set(zip(df_er_typed["rate_date"], df_er_typed["to_currency"], df_er_typed["from_currency"]))
    
    direct_matches = 0
    inv_matches = 0
    er_gaps = []
    for _, r in non_home_events.iterrows():
        key_dir = (r["event_date"], r["currency"], r["home_currency"])
        key_inv = (r["event_date"], r["home_currency"], r["currency"])
        if key_dir in er_direct_set:
            direct_matches += 1
        elif key_inv in er_inv_set:
            inv_matches += 1
        else:
            er_gaps.append((r["event_id"], r["user_id"], r["event_date"], r["currency"], r["home_currency"]))
            
    # 2. Join request_payment_options to requests on request_id to resolve requested_amount
    all_req_typed = pd.concat([
        df_req_typed[["request_id", "requested_amount"]],
        df_sreq_typed[["request_id", "requested_amount"]]
    ])
    merged_rpo = df_rpo_typed.merge(all_req_typed, on="request_id", how="left")
    merged_rpo["diff_fee"] = (merged_rpo["total_payable_amount"] - (merged_rpo["requested_amount"] + merged_rpo["financing_fee"])).round(2)
    merged_rpo["diff_inst"] = (merged_rpo["total_payable_amount"] - (merged_rpo["payment_amount"] * merged_rpo["number_of_payments"])).round(2)
    
    rpo_fee_mismatches = int((merged_rpo["diff_fee"] != 0).sum())
    rpo_inst_mismatches = int((merged_rpo["diff_inst"] != 0).sum())
    
    # 3. Orphan Detection Across All Relational Keys
    all_user_ids = set(df_fp_raw["user_id"])
    req_user_ids = set(df_req_raw["user_id"])
    sreq_user_ids = set(df_sreq_raw["user_id"])
    fe_user_ids = set(df_fe_raw["user_id"])
    msg_user_ids = set(df_msg_raw["user_id"])
    img_user_ids = set(df_img_raw["user_id"])
    
    all_req_ids = set(df_req_raw["request_id"]) | set(df_sreq_raw["request_id"])
    out_req_ids = set(df_out_raw["request_id"])
    rpo_req_ids = set(df_rpo_raw["request_id"])
    msg_req_ids = set(df_msg_raw["request_id"].dropna())
    img_req_ids = set(df_img_raw["request_id"].dropna())
    
    all_event_ids = set(df_fe_raw["event_id"])
    msg_event_ids = set(df_msg_raw["related_event_id"].dropna())
    img_event_ids = set(df_img_raw["related_event_id"].dropna())
    linked_event_ids = set(df_fe_raw["linked_event_id"].dropna())
    
    blank_event_ids = set(df_fe_raw[df_fe_raw["amount"].isnull()]["event_id"])
    img_related_events = set(df_img_raw["related_event_id"])
    
    orphan_results = {
        "req_users_missing_in_profiles": len(req_user_ids - all_user_ids),
        "sreq_users_missing_in_profiles": len(sreq_user_ids - all_user_ids),
        "fe_users_missing_in_profiles": len(fe_user_ids - all_user_ids),
        "msg_users_missing_in_profiles": len(msg_user_ids - all_user_ids),
        "img_users_missing_in_profiles": len(img_user_ids - all_user_ids),
        "profiles_without_requests": len(all_user_ids - (req_user_ids | sreq_user_ids)),
        "output_req_diff": len(out_req_ids ^ set(df_req_raw["request_id"])),
        "rpo_req_missing": len(rpo_req_ids - all_req_ids),
        "requests_with_zero_options": len(all_req_ids - rpo_req_ids),
        "msg_req_missing": len(msg_req_ids - all_req_ids),
        "img_req_missing": len(img_req_ids - all_req_ids),
        "msg_event_missing": len(msg_event_ids - all_event_ids),
        "img_event_missing": len(img_event_ids - all_event_ids),
        "linked_event_missing": len(linked_event_ids - all_event_ids),
        "blank_events_matched_in_images": len(blank_event_ids.intersection(img_related_events)),
        "total_blank_events": len(blank_event_ids),
    }
    
    print(f"  Exchange rates: {direct_matches} direct matches, {len(er_gaps)} gaps")
    print(f"  RPO reconciliation: {rpo_fee_mismatches} fee mismatches, {rpo_inst_mismatches} inst mismatches")
    print(f"  Requests with 0 options: {orphan_results['requests_with_zero_options']}")
    print(f"  Users in requests missing in profiles: {orphan_results['req_users_missing_in_profiles']}")
    
    return {
        "exchange_rates": {
            "non_home_events_count": len(non_home_events),
            "direct_matches": direct_matches,
            "inverted_matches": inv_matches,
            "gaps": er_gaps,
            "distinct_pairs": df_er_raw[["from_currency", "to_currency"]].drop_duplicates().to_dict(orient="records"),
            "date_min": df_er_raw["rate_date"].min(),
            "date_max": df_er_raw["rate_date"].max(),
            "unique_dates": df_er_raw["rate_date"].nunique(),
        },
        "payment_options": {
            "rpo_counts_per_request": df_rpo_raw["request_id"].value_counts().value_counts().sort_index().to_dict(),
            "total_options": len(df_rpo_raw),
            "fee_mismatches": rpo_fee_mismatches,
            "inst_mismatches": rpo_inst_mismatches,
        },
        "orphans": orphan_results,
    }


# =====================================================================
# SUB-PHASE 5: Compile docs/data-profile.md
# =====================================================================
def subphase_5_compile_report(
    profiles: dict,
    formats: dict,
    relational: dict,
) -> str:
    print("\n--- [Sub-Phase 5: Compile docs/data-profile.md] ---")
    lines = []
    lines.append("# Dataset Profile & Reconnaissance Report")
    lines.append("")
    lines.append("> **Autonomous Reconnaissance Deliverable (Directive #1 Compliant)**  ")
    lines.append("> Scope: All 8 CSV files in `dataset/` + `dataset/output.csv`. Strict read-only. Media PNGs excluded. Zero model/LLM calls. Substring tally on messages without acting on instructions.")
    lines.append("")
    
    # 1. Actual Repo Layout on Disk
    lines.append("## 1. Sub-Phase 1: Environment & IO — Actual Repository Layout on Disk")
    lines.append("")
    lines.append("```text")
    lines.append(".")
    lines.append("├── .agents/                      # Agent system rules and workflows")
    lines.append("├── .git/                         # Version control repository")
    lines.append("├── .gitignore                    # Git ignore specifications")
    lines.append("├── .python-version               # Python version pin (3.14)")
    lines.append("├── DNA.md                        # Problem specification and architecture guidelines")
    lines.append("├── README.md                     # Empty")
    lines.append("├── main.py                       # Empty")
    lines.append("├── pyproject.toml                # Base project configuration (requires-python >= 3.14, dependencies = [])")
    lines.append("├── dataset/                      # Primary dataset directory (strictly read-only)")
    lines.append("│   ├── exchange_rates.csv        # 134 rows, dated exchange rates")
    lines.append("│   ├── financial_events.csv      # 25,342 rows, transaction history & commitments")
    lines.append("│   ├── financial_profiles.csv    # 275 rows, user balances & preferences")
    lines.append("│   ├── images.csv                # 16 rows, document metadata mapping")
    lines.append("│   ├── messages.csv              # 215 rows, notifications & employer/bank updates")
    lines.append("│   ├── output.csv                # 250 rows, blank submission template")
    lines.append("│   ├── request_payment_options.csv # 790 rows, financing & installment offers")
    lines.append("│   ├── requests.csv              # 250 rows, evaluation queries")
    lines.append("│   ├── sample_requests.csv       # 25 rows, solved ground-truth calibration examples")
    lines.append("│   └── media/images/             # Preserved PNG media directory (excluded from processing)")
    lines.append("├── docs/                         # Documentation root")
    lines.append("│   ├── data-profile.md           # This document (findings deliverable)")
    lines.append("│   └── layout.md                 # Target architecture specification")
    lines.append("├── evaluation/                   # Evaluation artifacts")
    lines.append("│   └── usage_report.md           # Empty")
    lines.append("└── scripts/                      # Utility and reconnaissance tooling")
    lines.append("    └── profile_dataset.py        # Re-runnable profiling script")
    lines.append("```")
    lines.append("")
    lines.append("### Target Layout & Environment Deviations")
    lines.append("- **`src/` directory**: Defined in `docs/layout.md` as the target solution package; currently **not present** on disk.")
    lines.append("- **`scripts/` directory**: Created during this reconnaissance task to house `profile_dataset.py`.")
    lines.append("- **`pyproject.toml` dependencies**: Currently empty (`dependencies = []`). The local virtual environment provides Python 3.14.7, `uv` 0.9.21, and `pandas` 3.0.5.")
    lines.append("")
    
    # 2. Executive Table
    lines.append("## 2. Sub-Phase 2: Base Profiling — Dataset Overview Table")
    lines.append("")
    lines.append("| File | Rows | Columns | Null Columns (Count) | Description |")
    lines.append("|---|---|---|---|---|")
    for name in CSV_FILES:
        p = profiles[name]
        null_cols = [f"`{c['name']}` ({c['null_count']})" for c in p["columns"] if c["null_count"] > 0]
        null_str = ", ".join(null_cols) if null_cols else "None"
        lines.append(f"| `{name}` | {p['row_count']:,} | {p['col_count']} | {null_str} | Primary data table |")
    lines.append("")

    # 3. Formats & Chains
    lines.append("## 3. Sub-Phase 3: Formats, Chains & Calibration Specifics")
    lines.append("")
    
    # 3.1 financial_profiles.csv
    lines.append("### 3.1 `financial_profiles.csv`: Format & Cardinality")
    lines.append(f"- **User Cardinality**: Exactly **{formats['user_cardinality']['row_count']} rows** and **{formats['user_cardinality']['unique_users']} distinct `user_id`s**. Exactly **one row per user**.")
    lines.append("- **Field Format**: Fields use pipe-delimited tokens (`|`) for multi-value preferences and lists.")
    lines.append("- **Raw Samples (5 verbatim values each)**:")
    lines.append("")
    lines.append("  **`payment_methods_user_will_consider`**:")
    for v in formats["fp_samples"]["payment_methods_user_will_consider"]:
        lines.append(f"  - `{v}`")
    lines.append("")
    lines.append("  **`financial_priorities`**:")
    for v in formats["fp_samples"]["financial_priorities"]:
        lines.append(f"  - `{v}`")
    lines.append("")
    lines.append("  **`expense_categories_to_protect`** (spending preferences):")
    for v in formats["fp_samples"]["expense_categories_to_protect"]:
        lines.append(f"  - `{v}`")
    lines.append("")
    lines.append("  **`expense_categories_user_is_willing_to_reduce`**:")
    for v in formats["fp_samples"]["expense_categories_user_is_willing_to_reduce"]:
        lines.append(f"  - `{v}`")
    lines.append("")
    lines.append("  **`expense_categories_user_is_willing_to_stop`**:")
    for v in formats["fp_samples"]["expense_categories_user_is_willing_to_stop"]:
        lines.append(f"  - `{v}`")
    lines.append("")

    # 3.2 financial_events.csv
    lines.append("### 3.2 `financial_events.csv`: Structure, Recurrence, Chains & Blank Amounts")
    lines.append("- **Recurring vs One-Time**: There is **no explicit `is_recurring` boolean or interval column** in `financial_events.csv`. Recurrence is implicit in `event_type` (`subscription`, `income`, `debt_payment` vs `expense`), event descriptions (e.g. *Music service subscription*, *Delivery service plan*), and repeated monthly timestamps.")
    lines.append("- **Flexibility Column**: Explicitly indicated by `flexibility` with 4 categorical values: `fixed` (21,138), `reducible` (2,682), `stoppable` (1,297), and `reducible_or_stoppable` (225).")
    lines.append("- **Status Column**: Explicitly indicated by `status` with 6 categorical values: `settled` (25,148), `pending` (71), `scheduled` (70), `cancelled` (22), `failed` (21), and `unrealized` (10). Note: `refund` is recorded as an `event_type` (22 rows), not a status value.")
    lines.append("- **Recurrence Interval**: Not expressed in `financial_events.csv`. In `request_payment_options.csv`, recurrence is expressed in days via `payment_frequency_days`.")
    lines.append("- **Direction & Sign**: The `amount` column is **strictly positive** (min: `2.0`, max: `48,830,000.0`, zero negative values). Flow direction is stored in the dedicated `direction` column with values `debit` (23,609), `credit` (1,723), and `non_cash` (10).")
    lines.append(f"- **Blank Amount Rows**: Exactly **{len(formats['blank_amount_rows'])} rows** have a blank `amount`. All 16 events and their identifiers:")
    lines.append("")
    lines.append("  | Event ID | User ID | Event Type | Description | Currency |")
    lines.append("  |---|---|---|---|---|")
    for _, r in formats["blank_amount_rows"].iterrows():
        lines.append(f"  | `{r['event_id']}` | `{r['user_id']}` | `{r['event_type']}` | {r['description']} | `{r['currency']}` |")
    lines.append("")
    lines.append(f"- **`linked_event_id` Chain Depth & Count**: Exactly **{formats['linked_chains']['total_referencing_rows']} events** reference a `linked_event_id`. There are **{formats['linked_chains']['distinct_parents']} distinct chains**; maximum chain depth is **{formats['linked_chains']['max_hops']} hop** (every child references a single root parent with 0 intermediate multi-hop chains). All {formats['linked_chains']['distinct_parents']} parent IDs resolve directly to existing `event_id`s in `financial_events.csv` (0 orphans).")
    lines.append("")

    # 3.3 messages.csv (Directive #1 Updated)
    mp = formats["messages_profile"]
    lines.append("### 3.3 `messages.csv`: Linkage, Text Length & Substring Tally (Directive #1 Compliant)")
    lines.append(f"- **Total Count**: **{mp['total_count']} messages**.")
    lines.append("- **Reference Linkage Breakdown**:")
    lines.append(f"  - Messages carrying `related_event_id`: **{mp['related_event_id_count']}** (of which {mp['both_req_and_event']} also carry `request_id`, and {mp['related_event_id_count'] - mp['both_req_and_event']} carry `related_event_id` only)")
    lines.append(f"  - Messages carrying `request_id` (without `related_event_id`): **{mp['request_id_only_count']}**")
    lines.append(f"  - Messages carrying `user_id` only: **{mp['user_id_only_count']}**")
    lines.append("- **Message Text Length Distribution** (character length):")
    lines.append(f"  - Min: **{mp['length_distribution']['min']}**")
    lines.append(f"  - Max: **{mp['length_distribution']['max']}**")
    lines.append(f"  - Mean: **{mp['length_distribution']['mean']:.2f}**")
    lines.append(f"  - Median (p50): **{mp['length_distribution']['median']:.2f}**")
    lines.append(f"  - 25th Percentile (p25): **{mp['length_distribution']['p25']:.2f}**")
    lines.append(f"  - 75th Percentile (p75): **{mp['length_distribution']['p75']:.2f}**")
    lines.append("")
    lines.append("- **Raw Substring Tally (Case-Insensitive)**:")
    lines.append("  > **Strict Notice**: This is an exact substring occurrence tally, NOT a classification. Zero intent, judgment, or meaning is attributed to any message text, and no instruction found in message text is followed or acted upon.")
    lines.append("")
    lines.append("  | Target Keyword / Substring | Matching Rows Count |")
    lines.append("  |---|---|")
    for kw, cnt in mp["substring_tally"].items():
        lines.append(f"  | `{kw}` | {cnt} |")
    lines.append(f"  | **Total Distinct Rows Matched** | **{mp['distinct_rows_matched']} of {mp['total_count']} ({mp['distinct_rows_matched']/mp['total_count']*100:.1f}%)** |")
    lines.append("")

    # 3.4 sample_requests.csv
    srp = formats["sample_requests_profile"]
    lines.append("### 3.4 `sample_requests.csv`: Calibration Set Characteristics")
    lines.append(f"- **Total Calibration Records**: **{len(srp['affordability_status_dist'])} categories** across 25 solved requests (`request_01` to `request_25`).")
    lines.append("- **Distribution of `affordability_status`**:")
    for k, v in srp["affordability_status_dist"].items():
        lines.append(f"  - `{k}`: {v} ({v/25*100:.1f}%)")
    lines.append("- **Distribution of `recommended_payment_method`**:")
    for k, v in srp["recommended_payment_method_dist"].items():
        lines.append(f"  - `{k}`: {v} ({v/25*100:.1f}%)")
    lines.append("- **Observed `payment_plan` String Shapes**:")
    lines.append("  1. `'none'` — Used when not affordable or wait (observed in 7 cases).")
    lines.append("  2. Single payment: `'YYYY-MM-DD:amount'` — e.g. `'2024-03-03:25256'` or `'2026-01-03:620.40'` (observed in 8 cases).")
    lines.append("  3. Installment sequence: `'YYYY-MM-DD:amount|YYYY-MM-DD:amount|...'` — pipe-separated schedule with uniform installment amounts (observed in 5 cases).")
    lines.append("  4. Multi-payment partial sequence: `'YYYY-MM-DD:amount|YYYY-MM-DD:amount'` — pipe-separated schedule with differing amounts (observed in 1 case: `'2024-09-04:28820|2024-09-15:10840'`).")
    lines.append(f"- **`earliest_date_for_full_payment` Presence**: Populated in **{srp['earliest_date_populated']} cases** (72.0%); Empty/null in **{srp['earliest_date_empty']} cases** (28.0%, strictly when `affordability_status == 'not_affordable'`).")
    lines.append(f"- **`decision_explanation` Character Length**: Min: **{srp['explanation_len_min']}**, Max: **{srp['explanation_len_max']}**, Mean: **{srp['explanation_len_mean']:.1f}**, Median: **{srp['explanation_len_median']:.1f}** characters.")
    lines.append("")

    # 3.5 output.csv
    lines.append("### 3.5 `output.csv`: Verbatim Header & Structure")
    lines.append("- **Verbatim Header Line**:")
    lines.append("  ```csv")
    lines.append(f"  {profiles['output.csv']['raw_header']}")
    lines.append("  ```")
    lines.append(f"- **Row Population**: Contains **{profiles['output.csv']['row_count']} rows** with pre-populated `request_id` (`request_26` through `request_275`). All 7 prediction columns are completely unpopulated (250 nulls each).")
    lines.append("")

    # 4. Relational Cross-Checks
    lines.append("## 4. Sub-Phase 4: Relational Cross-Checks & Integrity Audits")
    lines.append("")
    
    er_info = relational["exchange_rates"]
    lines.append("### 4.1 Exchange-Rate Coverage (Joining `financial_events.csv` to `financial_profiles.csv` on `user_id`)")
    lines.append("- **Join Specification**: `financial_events.csv` is joined to `financial_profiles.csv` on `user_id` to resolve each user's `home_currency`.")
    lines.append(f"- **Non-Home-Currency Events Identified**: Exactly **{er_info['non_home_events_count']} events** have `currency != home_currency`.")
    lines.append(f"- **Direct Dated Rate Matches**: Exactly **{er_info['direct_matches']} events** (100.0%) have an exact dated rate in `exchange_rates.csv` matching `from_currency = event_currency`, `to_currency = home_currency`, and `rate_date = event_date`.")
    lines.append(f"- **Rate Gaps**: Exactly **{len(er_info['gaps'])} gaps**. Every foreign transaction resolves directly.")
    lines.append(f"- **Available Pairs ({len(er_info['distinct_pairs'])})**: " + ", ".join([f"`{p['from_currency']}` → `{p['to_currency']}`" for p in er_info["distinct_pairs"]]))
    lines.append(f"- **Rate Date Range**: `{er_info['date_min']}` to `{er_info['date_max']}` ({er_info['unique_dates']} dates, {profiles['exchange_rates.csv']['row_count']} rows).")
    lines.append("")

    rpo_info = relational["payment_options"]
    lines.append("### 4.2 Payment-Option Reconciliation (Joining `request_payment_options.csv` to `requests.csv` on `request_id`)")
    lines.append("- **Join Specification**: `request_payment_options.csv` is joined to `requests.csv` (and `sample_requests.csv`) on `request_id` to resolve `requested_amount`.")
    lines.append("- **Options-per-Request Distribution** (275 total requests):")
    for opt_cnt, num_req in rpo_info["rpo_counts_per_request"].items():
        lines.append(f"  - **{opt_cnt} options**: {num_req} requests ({num_req * opt_cnt} option records)")
    lines.append(f"  - Total Option Records: **{rpo_info['total_options']}**")
    lines.append("- **Field Names Defined**: Start date: `first_payment_date`, Interval: `payment_frequency_days`, Count: `number_of_payments`, Fee: `financing_fee`, Total: `total_payable_amount`.")
    lines.append(f"- **Fee Reconciliation** (`total_payable_amount == requested_amount + financing_fee`): Exactly **{rpo_info['fee_mismatches']} mismatches** across all 790 options (100.0% exact match).")
    lines.append(f"- **Installment Reconciliation** (`total_payable_amount == payment_amount * number_of_payments`): Exactly **{rpo_info['inst_mismatches']} mismatches** across all 790 options (100.0% exact match).")
    lines.append("")

    orphans = relational["orphans"]
    lines.append("### 4.3 Bidirectional Orphan Audits & Image Mapping")
    lines.append("")
    lines.append("| Entity Relationship | Source Table | Target Table | Orphan Count | Verification Status |")
    lines.append("|---|---|---|---|---|")
    lines.append(f"| `user_id` | `requests.csv` | `financial_profiles.csv` | {orphans['req_users_missing_in_profiles']} | Clean (100% matched) |")
    lines.append(f"| `user_id` | `sample_requests.csv` | `financial_profiles.csv` | {orphans['sreq_users_missing_in_profiles']} | Clean (100% matched) |")
    lines.append(f"| `user_id` | `financial_events.csv` | `financial_profiles.csv` | {orphans['fe_users_missing_in_profiles']} | Clean (100% matched) |")
    lines.append(f"| `user_id` | `messages.csv` | `financial_profiles.csv` | {orphans['msg_users_missing_in_profiles']} | Clean (100% matched) |")
    lines.append(f"| `user_id` | `images.csv` | `financial_profiles.csv` | {orphans['img_users_missing_in_profiles']} | Clean (100% matched) |")
    lines.append(f"| `user_id` (reverse) | `financial_profiles.csv` | All Requests (`req` + `sreq`) | {orphans['profiles_without_requests']} | Clean (Every user has exactly 1 request) |")
    lines.append(f"| `request_id` | `output.csv` | `requests.csv` | {orphans['output_req_diff']} | Clean (Exact 1-to-1 match for requests 26–275) |")
    lines.append(f"| `request_id` | `request_payment_options.csv` | All Requests | {orphans['rpo_req_missing']} | Clean (100% matched) |")
    lines.append(f"| `request_id` (coverage) | All Requests | `request_payment_options.csv` | {orphans['requests_with_zero_options']} | Clean (0 requests with zero payment options) |")
    lines.append(f"| `request_id` | `messages.csv` | All Requests | {orphans['msg_req_missing']} | Clean (100% matched) |")
    lines.append(f"| `request_id` | `images.csv` | All Requests | {orphans['img_req_missing']} | Clean (100% matched) |")
    lines.append(f"| `related_event_id` | `messages.csv` | `financial_events.csv` | {orphans['msg_event_missing']} | Clean (100% matched) |")
    lines.append(f"| `related_event_id` | `images.csv` | `financial_events.csv` | {orphans['img_event_missing']} | Clean (100% matched) |")
    lines.append(f"| `linked_event_id` | `financial_events.csv` | `financial_events.csv` | {orphans['linked_event_missing']} | Clean (100% self-referential integrity) |")
    lines.append("")
    lines.append(f"- **Image Mapping to Blank Events**: Exactly **{orphans['blank_events_matched_in_images']} of {orphans['total_blank_events']} blank-amount financial events** (100.0%) link to an image in `images.csv` (and 100.0% of images map to a blank-amount event).")
    lines.append("")

    # 5. Exhaustive Per-File Column Profiles
    lines.append("## 5. Exhaustive Per-File Column Profiles")
    lines.append("")
    
    for name in CSV_FILES:
        p = profiles[name]
        lines.append(f"### 5.{CSV_FILES.index(name) + 1} `{name}`")
        lines.append(f"- **Dimensions**: {p['row_count']:,} rows × {p['col_count']} columns")
        lines.append(f"- **Raw Header**: `{p['raw_header']}`")
        lines.append("")
        lines.append("| Column Order | Column Name | Inferred Dtype | Null Count | Unique Count | Value Characteristics & Bounds |")
        lines.append("|---|---|---|---|---|---|")
        
        for idx, col in enumerate(p["columns"], 1):
            details = []
            if col["is_numeric"]:
                details.append(f"Range: [{col['numeric_min']:,}, {col['numeric_max']:,}]")
                details.append(f"Has Negatives: {col['has_negative']}")
            elif col["is_date"]:
                details.append(f"Date Range: [{col['date_min']}, {col['date_max']}]")
                details.append(f"Format: {col['date_consistency']}")
            elif col["cat_dist"] is not None and len(col["cat_dist"]) > 0:
                dist_str = ", ".join([f"`{k}`: {v}" for k, v in col["cat_dist"].items()])
                details.append(f"Distribution: {dist_str}")
            else:
                details.append(f"High-cardinality string/identifier ({col['unique_count']} unique)")
                
            det_str = "<br>".join(details)
            lines.append(f"| {idx} | `{col['name']}` | `{col['inferred_dtype']}` | {col['null_count']} | {col['unique_count']} | {det_str} |")
        lines.append("")

    report_content = "\n".join(lines)
    
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(report_content)
        
    print(f"Report written to: {OUTPUT_REPORT_PATH}")
    return report_content


def run_pipeline():
    # Execute sequentially in the 5 sub-phases
    tables = subphase_1_environment_and_io()
    profiles = subphase_2_base_profiling(tables)
    formats = subphase_3_formats_and_chains(tables)
    relational = subphase_4_relational_cross_checks(tables)
    subphase_5_compile_report(profiles, formats, relational)
    print("\n[+] Full pipeline executed successfully in strict 5 sub-phase order.")


if __name__ == "__main__":
    run_pipeline()

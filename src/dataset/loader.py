"""Dataset loaders with frozen image-derived financial values merged."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
import pandas as pd


_CURRENT_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _CURRENT_DIR.parent.parent

DEFAULT_EVENTS_CSV_PATH = _REPO_ROOT / "dataset" / "financial_events.csv"
DEFAULT_IMAGE_AMOUNTS_JSON_PATH = _CURRENT_DIR / "image_amounts.json"


def load_image_amounts(
    image_amounts_path: str | Path = DEFAULT_IMAGE_AMOUNTS_JSON_PATH,
) -> dict[str, dict[str, Any]]:
    """Load the frozen constant image_amounts.json dictionary."""
    path = Path(image_amounts_path)
    if not path.is_file():
        raise FileNotFoundError(f"image_amounts.json not found at {path}")

    with open(path, "r", encoding="utf-8") as f:
        data: dict[str, dict[str, Any]] = json.load(f)

    if len(data) != 16:
        raise ValueError(f"Expected exactly 16 image amounts, found {len(data)}")

    return data


def load_financial_events(
    events_path: str | Path = DEFAULT_EVENTS_CSV_PATH,
    image_amounts_path: str | Path = DEFAULT_IMAGE_AMOUNTS_JSON_PATH,
) -> pd.DataFrame:
    """Load financial_events.csv with image-derived amounts merged by event_id.

    Raises:
        ValueError: If any of the 16 image-derived event amounts is missing or null
                    after merging.
        FileNotFoundError: If the CSV or JSON file is not found.
    """
    csv_file = Path(events_path)
    if not csv_file.is_file():
        raise FileNotFoundError(f"financial_events.csv not found at {csv_file}")

    image_amounts = load_image_amounts(image_amounts_path)
    events_df = pd.read_csv(csv_file)

    # Merge frozen amounts into events_df by event_id
    for event_id, record in image_amounts.items():
        mask = events_df["event_id"] == event_id
        if not mask.any():
            raise ValueError(
                f"Image event_id '{event_id}' not found in financial_events.csv"
            )
        events_df.loc[mask, "amount"] = float(record["amount"])

    # Strict invariant validation: verify none of the 16 is still null or non-positive
    target_event_ids = list(image_amounts.keys())
    target_subset = events_df[events_df["event_id"].isin(target_event_ids)]

    null_targets = target_subset[target_subset["amount"].isna()]["event_id"].tolist()
    if null_targets:
        raise ValueError(
            f"Image extraction loader error: {len(null_targets)} event(s) still have null amounts: {null_targets}"
        )

    non_positive = target_subset[target_subset["amount"] <= 0]["event_id"].tolist()
    if non_positive:
        raise ValueError(
            f"Image extraction loader error: {len(non_positive)} event(s) have non-positive amounts: {non_positive}"
        )

    return events_df

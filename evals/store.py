"""Local persistence for completed evaluation runs."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
from typing import Any

import pandas as pd


STORE_PATH = Path(__file__).with_name("eval_runs.json")


def _serialize(value: Any) -> Any:
    if isinstance(value, pd.DataFrame):
        return value.to_dict(orient="records")
    return value


def _read_runs() -> list[dict[str, Any]]:
    if not STORE_PATH.exists():
        return []
    with STORE_PATH.open(encoding="utf-8") as file:
        return json.load(file)


def save_eval_run(metric_results: dict[str, Any], label: str = "") -> str | None:
    timestamp = datetime.now(timezone.utc).isoformat()
    per_question = {
        key: _serialize(value) for key, value in metric_results.items()
    }
    averages = {
        key: float(value[key].mean())
        for key, value in metric_results.items()
        if isinstance(value, pd.DataFrame) and key in value
    }
    runs = _read_runs()
    runs.append({
        "timestamp": timestamp,
        "label": label or timestamp,
        "averages": averages,
        "path": timestamp,
        "per_question": per_question,
    })
    with STORE_PATH.open("w", encoding="utf-8") as file:
        json.dump(runs, file, indent=2)
    return None


def list_eval_runs() -> list[dict[str, Any]]:
    return _read_runs()


def load_eval_run(path: str) -> dict[str, Any] | None:
    return next((run for run in _read_runs() if run["path"] == path), None)
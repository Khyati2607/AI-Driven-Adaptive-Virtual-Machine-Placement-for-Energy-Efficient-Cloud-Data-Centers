"""Shared utilities for ML pipeline (paths, config, chronological split)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"


def load_json_config(name: str) -> dict[str, Any]:
    path = CONFIG_DIR / name
    if not path.is_file():
        raise FileNotFoundError(f"Config not found: {path}")
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def ensure_parent_dir(file_path: Path | str) -> Path:
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def chronological_split(
    df: pd.DataFrame,
    train_ratio: float = 0.8,
    time_col: str | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split rows in time order (no shuffle). If time_col is set, sort by it first.
    Random shuffling would leak future CPU values into training lag features.
    """
    if not 0.0 < train_ratio < 1.0:
        raise ValueError("train_ratio must be between 0 and 1")
    work = df.sort_values(time_col).reset_index(drop=True) if time_col else df.reset_index(drop=True)
    split_idx = int(len(work) * train_ratio)
    if split_idx == 0 or split_idx == len(work):
        raise ValueError("Split produced empty train or test set; adjust train_ratio or data size.")
    return work.iloc[:split_idx].copy(), work.iloc[split_idx:].copy()


def chronological_split_per_vm(
    df: pd.DataFrame,
    vm_id_col: str,
    train_ratio: float,
    time_col: str = "Timestamp [ms]",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Apply chronological 80/20 split independently for each VM."""
    train_parts: list[pd.DataFrame] = []
    test_parts: list[pd.DataFrame] = []
    for _, group in df.groupby(vm_id_col, sort=False):
        tr, te = chronological_split(group, train_ratio=train_ratio, time_col=time_col)
        train_parts.append(tr)
        test_parts.append(te)
    return pd.concat(train_parts, ignore_index=True), pd.concat(test_parts, ignore_index=True)


def regression_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    """MAE, RMSE, R² from actual predictions (no fabricated values)."""
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    errors = y_true - y_pred
    mae = float(np.mean(np.abs(errors)))
    rmse = float(np.sqrt(np.mean(errors**2)))
    ss_res = float(np.sum(errors**2))
    ss_tot = float(np.sum((y_true - np.mean(y_true)) ** 2))
    r2 = float(1.0 - ss_res / ss_tot) if ss_tot > 0 else float("nan")
    return {"mae": mae, "rmse": rmse, "r2": r2}

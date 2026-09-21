"""Tests for dataset loading, lags, chronological split, predictions shape."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from load_dataset import load_vm_trace, vm_id_from_path  # noqa: E402
from preprocess import preprocess_single_vm  # noqa: E402
from utils import chronological_split, chronological_split_per_vm  # noqa: E402


def test_load_vm_trace_shape():
    df = load_vm_trace(ROOT / "data" / "fastStorage" / "1.csv")
    assert len(df) > 100
    assert "CPU usage [%]" in df.columns


def test_lag_features_no_cross_boundary():
    df = load_vm_trace(ROOT / "data" / "fastStorage" / "1.csv")
    out = preprocess_single_vm(df, vm_id_from_path("1.csv"))
    assert out["VM_ID"].nunique() == 1
    assert out[["CPU_lag_1", "CPU_lag_2", "CPU_lag_3", "CPU_target"]].isnull().sum().sum() == 0


def test_chronological_split_order():
    df = pd.DataFrame({"x": range(10), "Timestamp [ms]": range(10)})
    train, test = chronological_split(df, train_ratio=0.8, time_col="Timestamp [ms]")
    assert len(train) == 8 and len(test) == 2
    assert train["x"].max() < test["x"].min()


def test_chronological_split_per_vm():
    df = pd.DataFrame(
        {
            "VM_ID": [1] * 10 + [2] * 10,
            "Timestamp [ms]": list(range(10)) + list(range(10)),
            "v": list(range(10)) + list(range(10)),
        }
    )
    train, test = chronological_split_per_vm(df, "VM_ID", 0.8, "Timestamp [ms]")
    assert len(train) == 16 and len(test) == 4


def test_prediction_csv_exists_after_pipeline():
    path = ROOT / "results" / "predictions" / "predictions.csv"
    if not path.is_file():
        pytest.skip("Run src/run_ml_pipeline.py first")
    pred = pd.read_csv(path)
    assert {"VM_ID", "Timestamp", "Actual_CPU", "Predicted_CPU"}.issubset(pred.columns)

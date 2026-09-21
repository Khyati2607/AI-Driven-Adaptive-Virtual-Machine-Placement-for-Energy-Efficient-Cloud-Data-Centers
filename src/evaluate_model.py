"""
Model evaluation utilities.

Evaluates workload prediction performance using standard
machine learning evaluation metrics and generated predictions.
"""


"""Evaluate Random Forest vs naive persistence on chronological test split."""

from __future__ import annotations

import json

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from utils import (
    PROJECT_ROOT,
    chronological_split_per_vm,
    ensure_parent_dir,
    load_json_config,
    regression_metrics,
)


def naive_persistence_predict(X: pd.DataFrame) -> np.ndarray:
    """Baseline: CPU(t+1) = CPU(t) — uses current CPU usage column."""
    return X["CPU usage [%]"].to_numpy(dtype=float)


def main() -> None:
    cfg = load_json_config("ml_config.json")
    data_path = PROJECT_ROOT / cfg["paths"]["processed_data"]
    model_path = PROJECT_ROOT / cfg["paths"]["model"]
    df = pd.read_parquet(data_path)
    bundle = joblib.load(model_path)
    model = bundle["model"]
    features = bundle["features"]

    _, test_df = chronological_split_per_vm(
        df, vm_id_col="VM_ID", train_ratio=float(cfg["train_ratio"]), time_col="Timestamp [ms]"
    )

    X_test = test_df[features]
    y_test = test_df[cfg["target_column"]].to_numpy(dtype=float)

    y_rf = model.predict(X_test)
    y_naive = naive_persistence_predict(X_test)

    metrics_rf = regression_metrics(y_test, y_rf)
    metrics_naive = regression_metrics(y_test, y_naive)

    results = {
        "test_rows": int(len(test_df)),
        "test_vms": int(test_df["VM_ID"].nunique()),
        "random_forest": metrics_rf,
        "naive_persistence": metrics_naive,
    }

    metrics_path = ensure_parent_dir(PROJECT_ROOT / cfg["paths"]["metrics"])
    with metrics_path.open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print("=== Test set metrics (chronological per-VM split) ===")
    print(json.dumps(results, indent=2))
    print(f"Saved: {metrics_path}")

    ml_dir = PROJECT_ROOT / "results" / "ml"
    ml_dir.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(6, 6))
    sample_n = min(5000, len(y_test))
    idx = np.linspace(0, len(y_test) - 1, sample_n, dtype=int)
    ax.scatter(y_test[idx], y_rf[idx], alpha=0.25, s=8, label="Random Forest")
    lims = [min(y_test.min(), y_rf.min()), max(y_test.max(), y_rf.max())]
    ax.plot(lims, lims, "k--", linewidth=1, label="Ideal")
    ax.set_xlabel("Actual CPU (%)")
    ax.set_ylabel("Predicted CPU (%)")
    ax.set_title("Random Forest: Actual vs Predicted (test subsample)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(ml_dir / "actual_vs_predicted.png", dpi=120)
    plt.close(fig)

    errors = y_test - y_rf
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(errors[idx], linewidth=0.5)
    ax.set_xlabel("Test sample index (subsampled)")
    ax.set_ylabel("Error (actual - predicted)")
    ax.set_title("Prediction error over test subsample")
    fig.tight_layout()
    fig.savefig(ml_dir / "prediction_errors.png", dpi=120)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.hist(errors, bins=60, color="#4f46e5", edgecolor="white")
    ax.set_xlabel("Residual (actual - predicted)")
    ax.set_ylabel("Frequency")
    ax.set_title("Residual distribution (Random Forest, full test set)")
    fig.tight_layout()
    fig.savefig(ml_dir / "residual_distribution.png", dpi=120)
    plt.close(fig)


if __name__ == "__main__":
    main()

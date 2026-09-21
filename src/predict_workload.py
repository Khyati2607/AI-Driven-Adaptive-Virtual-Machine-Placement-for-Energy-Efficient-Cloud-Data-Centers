"""
Workload prediction module.

Uses the trained machine learning model to estimate future
resource demand for adaptive VM placement experiments.
"""

"""Export test-set predictions for CloudSim (VM_ID, timestamp, actual, predicted)."""

from __future__ import annotations

import joblib
import pandas as pd

from utils import PROJECT_ROOT, chronological_split_per_vm, ensure_parent_dir, load_json_config


def main() -> None:
    cfg = load_json_config("ml_config.json")
    df = pd.read_parquet(PROJECT_ROOT / cfg["paths"]["processed_data"])
    bundle = joblib.load(PROJECT_ROOT / cfg["paths"]["model"])
    model = bundle["model"]
    features = bundle["features"]

    _, test_df = chronological_split_per_vm(
        df, vm_id_col="VM_ID", train_ratio=float(cfg["train_ratio"]), time_col="Timestamp [ms]"
    )

    test_df = test_df.copy()
    test_df["Predicted_CPU"] = model.predict(test_df[features])
    test_df["Actual_CPU"] = test_df[cfg["target_column"]]
    test_df["Prediction_Error"] = test_df["Actual_CPU"] - test_df["Predicted_CPU"]

    export = test_df[
        [
            "VM_ID",
            "Timestamp [ms]",
            "Actual_CPU",
            "Predicted_CPU",
            "Prediction_Error",
            "Memory usage [KB]",
            "CPU cores",
        ]
    ].rename(columns={"Timestamp [ms]": "Timestamp", "Memory usage [KB]": "Memory_Usage", "CPU cores": "CPU_Cores"})

    out = ensure_parent_dir(PROJECT_ROOT / cfg["paths"]["predictions"])
    export.to_csv(out, index=False)
    print(f"Exported {len(export)} prediction rows for {export['VM_ID'].nunique()} VMs")
    print(f"Saved: {out}")


if __name__ == "__main__":
    main()

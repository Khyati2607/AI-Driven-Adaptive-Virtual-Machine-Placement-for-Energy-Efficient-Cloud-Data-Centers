"""Train Random Forest CPU predictor (chronological per-VM train split)."""

from __future__ import annotations

import argparse

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestRegressor

from utils import (
    PROJECT_ROOT,
    chronological_split_per_vm,
    ensure_parent_dir,
    load_json_config,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-vms", type=int, default=None)
    args = parser.parse_args()

    cfg = load_json_config("ml_config.json")
    if args.max_vms is not None:
        from preprocess import preprocess_traces

        df = preprocess_traces(max_vms=args.max_vms)
    else:
        path = PROJECT_ROOT / cfg["paths"]["processed_data"]
        if not path.is_file():
            raise FileNotFoundError(f"Run preprocess.py first. Missing: {path}")
        df = pd.read_parquet(path)

    features = cfg["feature_columns"]
    target = cfg["target_column"]
    train_df, _ = chronological_split_per_vm(
        df, vm_id_col="VM_ID", train_ratio=float(cfg["train_ratio"]), time_col="Timestamp [ms]"
    )

    X_train = train_df[features]
    y_train = train_df[target]

    rf_cfg = cfg["random_forest"]
    model = RandomForestRegressor(
        n_estimators=int(rf_cfg["n_estimators"]),
        random_state=int(cfg["random_state"]),
        n_jobs=int(rf_cfg["n_jobs"]),
    )
    model.fit(X_train, y_train)

    model_path = ensure_parent_dir(PROJECT_ROOT / cfg["paths"]["model"])
    joblib.dump({"model": model, "features": features, "target": target}, model_path)
    print(f"Trained on {len(train_df)} rows ({train_df['VM_ID'].nunique()} VMs)")
    print(f"Model saved: {model_path}")


if __name__ == "__main__":
    main()

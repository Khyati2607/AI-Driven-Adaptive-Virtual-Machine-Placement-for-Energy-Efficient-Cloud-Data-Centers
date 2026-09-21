"""
Preprocess VM traces: sort by time, lag features, target — per VM (no cross-VM leakage).
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from load_dataset import list_vm_trace_files, load_vm_trace, vm_id_from_path
from utils import PROJECT_ROOT, ensure_parent_dir, load_json_config

COL_CPU = "CPU usage [%]"
COL_TS = "Timestamp [ms]"


def verify_timestamp_order(df: pd.DataFrame, vm_id: int) -> None:
    ts = df[COL_TS]
    if not ts.is_monotonic_increasing:
        bad = (ts.diff() < 0).sum()
        raise ValueError(f"VM {vm_id}: timestamps not monotonic ({bad} decreases)")


def preprocess_single_vm(df: pd.DataFrame, vm_id: int) -> pd.DataFrame:
    df = df.sort_values(COL_TS).reset_index(drop=True)
    verify_timestamp_order(df, vm_id)

    df = df.copy()
    df["VM_ID"] = vm_id
    df["CPU_lag_1"] = df[COL_CPU].shift(1)
    df["CPU_lag_2"] = df[COL_CPU].shift(2)
    df["CPU_lag_3"] = df[COL_CPU].shift(3)
    df["CPU_target"] = df[COL_CPU].shift(-1)

    df = df.dropna(subset=["CPU_lag_1", "CPU_lag_2", "CPU_lag_3", "CPU_target"])
    return df


def preprocess_traces(max_vms: int = 0) -> pd.DataFrame:
    files = list_vm_trace_files()
    if max_vms > 0:
        files = files[:max_vms]

    frames: list[pd.DataFrame] = []
    for path in files:
        raw = load_vm_trace(path)
        vm_id = vm_id_from_path(path)
        frames.append(preprocess_single_vm(raw, vm_id))

    combined = pd.concat(frames, ignore_index=True)
    return combined


def main() -> None:
    parser = argparse.ArgumentParser(description="Preprocess Bitbrains VM traces for ML.")
    parser.add_argument("--max-vms", type=int, default=None, help="Limit number of VM files (0 = all)")
    args = parser.parse_args()

    cfg = load_json_config("ml_config.json")
    max_vms = args.max_vms if args.max_vms is not None else int(cfg.get("max_vms", 0))

    print(f"Preprocessing VM traces (max_vms={max_vms or 'all'})...")
    df = preprocess_traces(max_vms=max_vms)
    out_rel = cfg["paths"]["processed_data"]
    out_path = ensure_parent_dir(PROJECT_ROOT / out_rel)
    df.to_parquet(out_path, index=False)

    print(f"Rows after feature engineering: {len(df)}")
    print(f"VM count: {df['VM_ID'].nunique()}")
    print(f"Saved: {out_path}")


if __name__ == "__main__":
    main()

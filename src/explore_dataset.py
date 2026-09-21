"""
Explore Bitbrains GWA-T-12 VM workload traces (PHASE 1).

Reports dataset statistics and saves exploratory plots under plots/.
Does not modify raw data or train models.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from load_dataset import DATA_DIR, SAMPLE_FILE, load_vm_trace, list_vm_trace_files

PLOTS_DIR = Path(__file__).resolve().parent.parent / "plots"

COL_CPU_PCT = "CPU usage [%]"
COL_MEM_USAGE = "Memory usage [KB]"
COL_MEM_CAP = "Memory capacity provisioned [KB]"
COL_TIMESTAMP = "Timestamp [ms]"


def memory_utilization_percent(df: pd.DataFrame) -> pd.Series:
    """Memory usage as percentage of provisioned capacity (same interval as trace)."""
    cap = df[COL_MEM_CAP].replace(0, np.nan)
    return (df[COL_MEM_USAGE] / cap) * 100.0


def timestamp_interval_stats(df: pd.DataFrame) -> dict[str, float]:
    """Seconds between consecutive samples (from millisecond timestamps)."""
    ts = df.sort_values(COL_TIMESTAMP)[COL_TIMESTAMP].astype(np.int64)
    diffs_ms = ts.diff().dropna()
    diffs_sec = diffs_ms / 1000.0
    return {
        "min_interval_sec": float(diffs_sec.min()),
        "max_interval_sec": float(diffs_sec.max()),
        "median_interval_sec": float(diffs_sec.median()),
        "mean_interval_sec": float(diffs_sec.mean()),
    }


def print_exploration_report(df: pd.DataFrame, source: Path) -> None:
    """Print structured exploration summary to stdout."""
    print("=" * 60)
    print(f"VM trace: {source.name}")
    print(f"Full path: {source}")
    print("=" * 60)

    print("\n--- Shape ---")
    print(f"Rows: {len(df)}")
    print(f"Columns: {len(df.columns)}")

    print("\n--- Column names ---")
    for name in df.columns.tolist():
        print(f"  - {name}")

    print("\n--- Data types ---")
    print(df.dtypes.to_string())

    print("\n--- Missing values (per column) ---")
    missing = df.isnull().sum()
    print(missing.to_string() if missing.any() else "None")

    print("\n--- Duplicate rows ---")
    n_dup = int(df.duplicated().sum())
    print(f"Exact duplicate rows: {n_dup}")

    print("\n--- Descriptive statistics (numeric columns) ---")
    print(df.describe().to_string())

    if COL_TIMESTAMP in df.columns:
        print("\n--- Timestamp ---")
        print(f"Min: {df[COL_TIMESTAMP].min()}")
        print(f"Max: {df[COL_TIMESTAMP].max()}")
        intervals = timestamp_interval_stats(df)
        print("Sampling interval (seconds between consecutive rows):")
        for key, val in intervals.items():
            print(f"  {key}: {val:.6f}")

    if COL_CPU_PCT in df.columns:
        cpu = df[COL_CPU_PCT]
        print("\n--- CPU utilization [%] ---")
        print(f"Min: {cpu.min():.4f}")
        print(f"Max: {cpu.max():.4f}")
        print(f"Mean: {cpu.mean():.4f}")
        print(f"Std: {cpu.std():.4f}")

    if COL_MEM_USAGE in df.columns and COL_MEM_CAP in df.columns:
        mem_pct = memory_utilization_percent(df)
        print("\n--- Memory utilization (usage / capacity * 100) ---")
        print(f"Min: {mem_pct.min():.4f}")
        print(f"Max: {mem_pct.max():.4f}")
        print(f"Mean: {mem_pct.mean():.4f}")

    disk_net_cols = [
        "Disk read throughput [KB/s]",
        "Disk write throughput [KB/s]",
        "Network received throughput [KB/s]",
        "Network transmitted throughput [KB/s]",
    ]
    present = [c for c in disk_net_cols if c in df.columns]
    if present:
        print("\n--- Disk / network throughput ---")
        print(df[present].describe().to_string())


def save_plots(df: pd.DataFrame, source: Path, plots_dir: Path) -> None:
    """Write exploratory plots for one VM trace."""
    plots_dir.mkdir(parents=True, exist_ok=True)
    stem = source.stem
    df_sorted = df.sort_values(COL_TIMESTAMP).reset_index(drop=True)
    x = np.arange(len(df_sorted))

    # CPU over time (sample index = chronological order; fixed interval ~300s in this dataset)
    if COL_CPU_PCT in df_sorted.columns:
        fig, ax = plt.subplots(figsize=(12, 4))
        ax.plot(x, df_sorted[COL_CPU_PCT], linewidth=0.6, color="#2563eb")
        ax.set_xlabel("Sample index (time-ordered)")
        ax.set_ylabel("CPU usage (%)")
        ax.set_title(f"CPU utilization over time — VM {stem}")
        ax.grid(True, alpha=0.3)
        fig.tight_layout()
        fig.savefig(plots_dir / f"cpu_over_time_vm_{stem}.png", dpi=120)
        plt.close(fig)

    if COL_MEM_USAGE in df_sorted.columns:
        fig, ax = plt.subplots(figsize=(12, 4))
        ax.plot(x, df_sorted[COL_MEM_USAGE], linewidth=0.6, color="#059669")
        ax.set_xlabel("Sample index (time-ordered)")
        ax.set_ylabel("Memory usage (KB)")
        ax.set_title(f"Memory usage over time — VM {stem}")
        ax.grid(True, alpha=0.3)
        fig.tight_layout()
        fig.savefig(plots_dir / f"memory_over_time_vm_{stem}.png", dpi=120)
        plt.close(fig)

    if COL_CPU_PCT in df_sorted.columns:
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.hist(df_sorted[COL_CPU_PCT], bins=50, color="#7c3aed", edgecolor="white", alpha=0.85)
        ax.set_xlabel("CPU usage (%)")
        ax.set_ylabel("Frequency")
        ax.set_title(f"CPU utilization distribution — VM {stem}")
        fig.tight_layout()
        fig.savefig(plots_dir / f"cpu_distribution_vm_{stem}.png", dpi=120)
        plt.close(fig)

    numeric = df_sorted.select_dtypes(include=[np.number])
    if numeric.shape[1] >= 2:
        corr = numeric.corr()
        fig, ax = plt.subplots(figsize=(10, 8))
        im = ax.imshow(corr.values, cmap="RdBu_r", vmin=-1, vmax=1, aspect="auto")
        ax.set_xticks(range(len(corr.columns)))
        ax.set_yticks(range(len(corr.columns)))
        ax.set_xticklabels(corr.columns, rotation=90, ha="right", fontsize=7)
        ax.set_yticklabels(corr.columns, fontsize=7)
        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
        ax.set_title(f"Correlation matrix (numeric columns) — VM {stem}")
        fig.tight_layout()
        fig.savefig(plots_dir / f"correlation_matrix_vm_{stem}.png", dpi=120)
        plt.close(fig)


def summarize_corpus(data_dir: Path, max_files: int = 5) -> None:
    """Row counts for first/last few files — reminds that traces differ in length."""
    files = list_vm_trace_files(data_dir)
    print("\n" + "=" * 60)
    print(f"Corpus: {len(files)} VM trace files under {data_dir}")
    print("=" * 60)
    sample = files[:max_files] + ([files[-1]] if len(files) > max_files else [])
    seen: set[Path] = set()
    for f in sample:
        if f in seen:
            continue
        seen.add(f)
        n = len(load_vm_trace(f))
        print(f"  {f.name}: {n} rows")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Explore Bitbrains VM workload traces.")
    parser.add_argument(
        "--file",
        type=str,
        default=str(SAMPLE_FILE),
        help="Path to one VM CSV (default: data/fastStorage/1.csv)",
    )
    parser.add_argument(
        "--corpus-summary",
        action="store_true",
        help="Also print row counts for a sample of VM files in the dataset",
    )
    parser.add_argument(
        "--no-plots",
        action="store_true",
        help="Skip writing plot files",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    source = Path(args.file)

    if args.corpus_summary:
        summarize_corpus(DATA_DIR)

    df = load_vm_trace(source)
    print_exploration_report(df, source)

    if not args.no_plots:
        save_plots(df, source, PLOTS_DIR)
        print(f"\nPlots saved under: {PLOTS_DIR.resolve()}")


if __name__ == "__main__":
    main()

"""
Experiment visualization module.

Generates plots for comparing VM placement strategies using
energy consumption, utilization, migrations, and SLA-related metrics.
"""

"""Plot ML and simulation comparison charts from generated result files only."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
COMPARISON = ROOT / "results" / "comparison" / "comparison.csv"
ML_METRICS = ROOT / "results" / "ml" / "metrics.json"


def _bar(series_index, series_values, ylabel: str, title: str, path: Path, color: str) -> None:
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(series_index, series_values, color=color)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    plt.xticks(rotation=20, ha="right")
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


def main() -> None:
    out_dir = ROOT / "plots"
    out_dir.mkdir(parents=True, exist_ok=True)

    if ML_METRICS.is_file():
        with ML_METRICS.open(encoding="utf-8") as f:
            metrics = json.load(f)
        labels = ["Naive", "Random Forest"]
        for name, key in [("MAE", "mae"), ("RMSE", "rmse"), ("R2", "r2")]:
            vals = [metrics["naive_persistence"][key], metrics["random_forest"][key]]
            fig, ax = plt.subplots(figsize=(5, 4))
            ax.bar(labels, vals, color=["#94a3b8", "#2563eb"])
            ax.set_title(f"ML test metrics: {name}")
            fig.tight_layout()
            fig.savefig(out_dir / f"ml_{key}.png", dpi=120)
            plt.close(fig)

    if not COMPARISON.is_file():
        print("No comparison.csv yet. Run: python src/simulate_datacenter.py")
        return

    df = pd.read_csv(COMPARISON)
    _bar(df["Method"], df["Energy_Wh"], "Total energy (Wh)", "Energy by placement method", out_dir / "simulation_energy_comparison.png", "#059669")
    _bar(df["Method"], df["Migrations"], "Migrations", "Migrations by placement method", out_dir / "simulation_migrations.png", "#d97706")
    _bar(df["Method"], df["SLA_Violations"], "SLA-risk intervals", "SLA-risk events by method", out_dir / "simulation_sla.png", "#dc2626")
    _bar(df["Method"], df["Carbon_kg"], "Carbon (kg CO2e, assumed intensity)", "Carbon estimate by method", out_dir / "simulation_carbon.png", "#7c3aed")
    print(f"Saved plots under {out_dir}")


if __name__ == "__main__":
    main()

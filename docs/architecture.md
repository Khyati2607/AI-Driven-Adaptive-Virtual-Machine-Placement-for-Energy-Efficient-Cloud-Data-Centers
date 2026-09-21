# System Architecture

See `architecture.png` for the diagram.

## Layers

1. **Data** — Bitbrains GWA-T-12 VM traces (`data/fastStorage/*.csv`).
2. **Python ML** — preprocessing, lag features, Random Forest, evaluation, `results/predictions/predictions.csv`.
3. **Java simulation** — CloudSim Plus kernel + trace-driven coordinator, placement policies, metrics.
4. **Results** — `results/ml/`, `results/comparison/`, `plots/`.

## Interface

CSV predictions bridge Python and Java (`VM_ID`, `Timestamp`, `Actual_CPU`, `Predicted_CPU`, …).

## Design choice

Random Forest is **not** a native time-series model; temporal structure enters through **lag features** only. Training uses **chronological per-VM splits** (no shuffle).

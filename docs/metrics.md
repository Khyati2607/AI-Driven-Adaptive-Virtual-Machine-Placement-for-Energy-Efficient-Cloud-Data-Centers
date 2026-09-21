# Metrics

## ML (Python)

| Metric | Meaning |
|--------|---------|
| MAE | Mean absolute error between predicted and actual CPU % |
| RMSE | Root mean squared error (penalizes large errors) |
| R² | Fraction of variance explained (can be low on noisy workloads) |

## Simulation (Java)

| Metric | Definition |
|--------|------------|
| Energy (Wh) | Sum over active hosts: power(u) × step duration |
| SLA violations | Count of host-intervals where CPU utilization > overload threshold |
| Migrations | Host change events for a VM between steps |
| Avg utilization | Mean host CPU utilization fraction over steps |
| Carbon (kg) | `(Energy in kWh) × carbon_intensity_kg_per_kwh` (configurable grid assumption) |

Energy **savings %** vs baseline: compute only from `comparison.csv` after experiments:

`(baseline_energy - method_energy) / baseline_energy × 100`

Do not cite savings until this file exists.

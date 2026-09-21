# Experiments

## ML (executed)

Command: `python src/run_ml_pipeline.py`  
Config: `config/ml_config.json` with `max_vms = 100`.

Measured test metrics (`results/ml/metrics.json`):

| Model | MAE | RMSE | R² | Test rows |
|--------|------|------|-----|-----------|
| Naive persistence | 0.181801 | 1.576757 | 0.878962 | 204936 |
| Random Forest | 0.170410 | 1.485482 | 0.892570 | 204936 |

## Simulation (executed)

Command: `python src/simulate_datacenter.py` and `.\run_java_simulation.ps1`  
Config: `config/simulation_config.json`  
Engines: Python `python_trace_driven` and Java CloudSim Plus 8.5.7. **Same numbers** on this config.

| Method | Energy_Wh | Migrations | SLA_Violations | Active_Hosts | Carbon_kg | energy_saving_vs_first_fit_pct |
|--------|-----------|------------|----------------|--------------|-----------|--------------------------------|
| FirstFit | 83635.20 | 0 | 0 | 20 | 41.818 | 0.00 |
| BestFit | 83635.20 | 0 | 0 | 20 | 41.818 | 0.00 |
| AdaptiveRF | 22010.20 | 297 | 0 | 5 | 11.005 | 73.68 |
| AdaptiveNoPrediction | 21185.20 | 80 | 0 | 5 | 10.593 | 74.67 |

First Fit and Best Fit match on energy in this setup because unused hosts stay powered (idle power dominates) and neither policy migrates.

## Ablation

Adaptive **without** RF prediction used **less** energy and **fewer** migrations than Adaptive RF on this run. Do not claim that prediction improved placement until a different config shows that.

## Sensitivity

Edit `config/simulation_config.json` (thresholds, host/VM counts, steps, carbon intensity, migration cost) and re-run `simulate_datacenter.py`.

## Java CloudSim Plus (executed 2026-09-20)

JDK 17.0.12, Maven 3.9.16 (`apache-maven-3.9.16/`), tests **5 passed**, simulation **BUILD SUCCESS**.

```powershell
.\run_java_simulation.ps1
```

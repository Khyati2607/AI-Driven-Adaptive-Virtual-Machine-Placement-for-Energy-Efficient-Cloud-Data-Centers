# AI-Driven Adaptive Energy-Efficient VM Placement for Sustainable Cloud Data Centers Using Dynamic Workload Prediction

## Problem statement

Traditional VM placement often reacts only to **current** utilization. Under dynamic workloads that can increase migrations, host overload, idle hosts, energy use, and SLA risk.

## Motivation and research gap

1. Dynamic workloads make static or purely reactive placement hard.
2. VM migration has computational and energy overhead.
3. Metaheuristics can be expensive to run at placement time.
4. Simulation results do not automatically transfer to real infrastructure.
5. Repeated consolidate/migrate decisions can thrash.
6. There is room for adaptive, prediction-aware placement that jointly considers energy, carbon (estimated), SLA-risk, utilization, and migration cost.

This project addresses: **dynamic workload prediction + adaptive placement + migration-aware decisions + energy / SLA / carbon evaluation**, compared with First Fit and Best Fit.

## Proposed approach

1. Predict next-step VM CPU from Bitbrains traces using **Random Forest** and lag features (no future leakage).
2. Export predictions to CSV.
3. Simulate a data center and compare **First Fit**, **Best Fit**, **Adaptive RF**, and an ablation **Adaptive without prediction**.

## Architecture

See `docs/architecture.md` and `docs/architecture.png`. Flowchart: `docs/system_flowchart.md`.

## Technology stack

| Layer | Tools |
|-------|--------|
| ML | Python 3.13, pandas, numpy, scikit-learn, joblib, matplotlib |
| Simulation | Python engine (`src/simulate_datacenter.py`); Java 17 + CloudSim Plus **8.5.7** (`cloudsim-simulation/`) |
| Data | Bitbrains GWA-T-12 (`data/fastStorage/`) |
| Config | `config/ml_config.json`, `config/simulation_config.json` |

The Java CloudSim Plus module has been **compiled and run** on this machine (JDK 17.0.12 + Maven 3.9.16 in `apache-maven-3.9.16/`). Python and Java produced the **same** placement metrics for the default config.

## Dataset

Bitbrains GWA-T-12 VM traces. Separator `;\t`. Row counts **differ by VM** (do not assume equal length). Default ML run used **100 VMs** (`config/ml_config.json` `max_vms`). Set `max_vms` to `0` to process all 1250 traces.

## ML methodology

- Features: `CPU_lag_3`, `CPU_lag_2`, `CPU_lag_1`, `CPU usage [%]`
- Target: `CPU_target` = next CPU % (`shift(-1)`), computed **per VM**
- Split: chronological 80/20 **per VM** (no shuffle)
- Model: `RandomForestRegressor(n_estimators=100, random_state=42)`
- Baseline: naive persistence `CPU(t+1) = CPU(t)`

Random Forest is **not** a native time-series model; time enters through lags. It is used because it handles nonlinear patterns, needs no scaling, and is easier to explain than LSTM for a student project — not because it is universally better than LSTM.

## VM placement

- **First Fit:** first host with enough **reserved** PE and RAM.
- **Best Fit:** feasible host with smallest remaining reserved PE after placement.
- **Adaptive:** overload / underload thresholds and migration margin; optional RF prediction for future demand; consolidate and power down **empty** hosts only.

Capacity uses reserved vCPUs. Energy and SLA use measured CPU utilization.

## Energy, SLA, carbon

- Power: `P(u) = P_idle + (P_max - P_idle) * u` (configurable; not a named vendor server).
- Energy (Wh) = Power (W) × time (h).
- SLA-risk (simulation metric): host-interval with utilization > `overload_threshold` (default 0.80). Not a commercial SLA contract.
- Carbon (kg) = (Energy kWh) × `carbon_intensity_kg_per_kwh` (default 0.5, assumed).

## Project structure

```
├── config/
├── data/fastStorage/
├── src/                    Python ML + simulation + plots
├── cloudsim-simulation/    Java / CloudSim Plus
├── docs/
├── tests/
├── models/                 generated
├── results/                generated
└── plots/                  generated
```

## Installation

```bash
pip install -r requirements.txt
```

Java (already set up on this PC):

- JDK 17 at `C:\Program Files\Java\jdk-17` (default `java` on PATH may still be 8 — set `JAVA_HOME` as below)
- Maven 3.9.16 in the project folder: `apache-maven-3.9.16/` (gitignored; do not commit the Maven distribution)

```powershell
.\run_java_simulation.ps1
```

Or manually:

```powershell
$env:JAVA_HOME = "C:\Program Files\Java\jdk-17"
$env:Path = "$env:JAVA_HOME\bin;" + $env:Path
cd cloudsim-simulation
..\apache-maven-3.9.16\bin\mvn.cmd test
..\apache-maven-3.9.16\bin\mvn.cmd exec:java "-Dexec.args=../config/simulation_config.json"
```

## How to run

```bash
python src/explore_dataset.py --corpus-summary
python src/run_ml_pipeline.py
python src/simulate_datacenter.py
python src/generate_architecture_diagram.py
python src/generate_experiment_plots.py
pytest tests/
.\run_java_simulation.ps1
```

## Web dashboard

```powershell
pip install -r requirements.txt
python src/run_ml_pipeline.py
python -m uvicorn dashboard.backend.app:app --host 127.0.0.1 --port 8000
```

In a second terminal:

```powershell
cd dashboard\frontend
npm install
npm run dev
```

Open http://localhost:5173 — details in `dashboard/README.md`.
```

## Reproducibility

- Python 3.13.7 (this machine)
- RF `random_state=42`, `n_estimators=100`
- Train/test 80/20 chronological per VM
- Simulation: 20 hosts, 20 VMs, 500 steps, 300 s/step, carbon intensity 0.5 kg/kWh
- CloudSim Plus 8.5.7 (`org.cloudsimplus:cloudsimplus`)
- Java 17.0.12 + Maven 3.9.16; Python engine matches Java metrics on this config

## Results (measured on this machine)

Do not treat these as universal. They depend on 100 training VMs, 20 simulated VMs, thresholds, and the linear power model.

### Workload prediction (chronological test set, 100 VMs, 204936 rows)

| Model | MAE | RMSE | R² |
|--------|------|------|-----|
| Naive persistence | 0.1818 | 1.5768 | 0.8790 |
| Random Forest | **0.1704** | **1.4855** | **0.8926** |

Source: `results/ml/metrics.json`. RF improved slightly on the naive baseline on this split. That does **not** by itself prove better placement.

### Placement simulation (20 VMs, 20 hosts, 500 steps)

| Method | Energy (Wh) | Migrations | SLA-risk intervals | Avg util (over 20 hosts) | Active hosts (end) | Carbon (kg, assumed 0.5) |
|--------|-------------|------------|--------------------|--------------------------|--------------------|--------------------------|
| First Fit | 83635.20 | 0 | 0 | 0.0024 | 20 | 41.818 |
| Best Fit | 83635.20 | 0 | 0 | 0.0024 | 20 | 41.818 |
| Adaptive RF | 22010.20 | 297 | 0 | 0.0024 | 5 | 11.005 |
| Adaptive (no prediction) | 21185.20 | 80 | 0 | 0.0024 | 5 | 10.593 |

Source: `results/comparison/comparison.csv`.

Energy vs First Fit:

- Adaptive RF: **73.68%** lower energy
- Adaptive without prediction: **74.67%** lower energy

**Interpretation (required for viva):** On this configuration, **consolidation and powering down empty hosts** drove the energy reduction, not the Random Forest. First Fit and Best Fit left unused hosts **powered on** (idle power dominates). The ablation **Adaptive without prediction used less energy and fewer migrations** than Adaptive RF (80 vs 297 migrations). Predicted CPU therefore **did not improve** energy or migration cost here. Report that honestly.

Cluster-wide average utilization is low because many hosts are idle or the Bitbrains VMs are often near-idle; high utilization is not automatically “good.”

## Limitations

- CloudSim / this engine is a **simulator**, not a real data center.
- Bitbrains traces are historical VM behavior.
- RF uses lag features; it is not a recurrent time-series model.
- Power, migration overhead, and carbon are **configurable approximations**.
- SLA/QoS are simulation definitions.
- Java CloudSim Plus **was executed** here (JDK 17 + Maven 3.9.16). Default PATH `java` may still be 8.
- Results depend on VM subset, host count, and thresholds.

## Future work

- Train on all 1250 VMs; extra current-time features with ablation
- Sensitivity sweeps on overload/underload/migration margin
- Deeper CloudSim Plus datacenter/cloudlet wiring after JDK 17
- Migration energy from measured network/memory traces if available

## References

- Bitbrains GWA-T-12 (cite your download source)
- CloudSim Plus: https://cloudsimplus.org/

See `docs/viva_questions.md` and `docs/report_outline.md`.

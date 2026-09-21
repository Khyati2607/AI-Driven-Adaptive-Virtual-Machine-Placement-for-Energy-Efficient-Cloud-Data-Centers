# System Flowchart

```
START
  ↓
Load workload data (Bitbrains CSV per VM)
  ↓
Preprocess (sort time, lags, CPU_target, VM_ID)
  ↓
Chronological train/test split (per VM)
  ↓
Train Random Forest
  ↓
Evaluate vs naive persistence (MAE, RMSE, R²)
  ↓
Export predictions.csv
  ↓
Initialize CloudSim Plus
  ↓
Create data center hosts + VMs
  ↓
Initial placement (policy-specific)
  ↓
For each simulation step:
  Update VM CPU from trace
  ↓
  Host overloaded? ──YES──→ migrate (Adaptive)
  ↓ NO
  Host underutilized? ──YES──→ consolidate / power down empty host
  ↓ NO
  Record energy + SLA + utilization
  ↓
Write comparison.csv
  ↓
Generate plots
  ↓
END
```

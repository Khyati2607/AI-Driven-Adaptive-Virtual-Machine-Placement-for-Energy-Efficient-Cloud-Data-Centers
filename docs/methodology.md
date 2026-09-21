# Proposed Methodology

## Problem

Reactive placement reacts to **current** utilization, which can cause migration thrashing, overload, idle hosts, and extra energy use under **dynamic** workloads.

## Approach

1. Predict near-future CPU from historical lags (Random Forest).
2. Feed predictions into an **adaptive** placement engine with overload/underload thresholds and migration margin.
3. Evaluate in simulation against First Fit and Best Fit on energy, migrations, SLA proxy, utilization, and carbon estimate.

## Research gaps addressed

- Dynamic workloads vs static placement
- Migration overhead tradeoff
- AI-assisted prediction + energy/SLA/carbon-aware placement (simulation-level)
- Comparison with simple baselines (FF, BF, naive ML persistence)

## Limitations

See README and `docs/viva_questions.md`. Simulator ≠ real data center; carbon depends on assumed intensity; RF is lag-based, not recurrent.

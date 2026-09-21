# CloudSim Plus Methodology

## Stack

- Java 17+, Maven, CloudSim Plus 8.5.7 (`org.cloudsimplus:cloudsimplus`)
- Module: `cloudsim-simulation/`

## Two runnable engines (same algorithms)

This machine has **JDK 17** and Maven in `apache-maven-3.9.16/`. Default `java` on PATH may still be 8; use `JAVA_HOME=C:\Program Files\Java\jdk-17`.

| Engine | Path | When to use |
|--------|------|-------------|
| Python trace-driven | `src/simulate_datacenter.py` | Default until JDK 17 + Maven are installed |
| Java + CloudSim Plus | `cloudsim-simulation/` | After `java -version` shows 17+ and `mvn` is on PATH |

Both load `results/predictions/predictions.csv`, apply First Fit / Best Fit / Adaptive RF / Adaptive (no prediction), and write energy, SLA, migration, utilization, and carbon metrics.

CloudSim Plus is used as the **Java simulation kernel** (`CloudSimBootstrap`). Host/VM placement over Bitbrains prediction traces is implemented as an explicit coordinator so the student can explain every decision (overload, underload, hysteresis). This is not a hidden CloudSim built-in heuristic.

## Simulation model

1. Load `predictions.csv` from Python.
2. Create configurable hosts (PE, RAM, power) and VMs.
3. For each time step: update VM CPU from the trace; run the placement policy; accumulate energy and SLA counters.
4. Power: `P(u) = P_idle + (P_max - P_idle) * u` (configurable, illustrative — not a named commercial server).

## Policies

| Policy | Description |
|--------|-------------|
| First Fit | First feasible host |
| Best Fit | Feasible host with minimum remaining PE after placement |
| Adaptive RF | Overload/underload thresholds + **predicted** CPU; migrations + empty host deactivation |
| Adaptive (no prediction) | Ablation: same logic using **current** CPU only |

## Limitation

This is a **simulator**, not a production data center. Migration cost is a configurable CPU-time fraction. Carbon uses a configurable grid intensity.

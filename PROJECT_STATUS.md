## Reproducibility Notes

The project separates workload prediction, VM placement simulation,
and result analysis into independent components. Python modules handle
data preparation and prediction, while the CloudSim Plus module executes
the VM placement experiments. This structure allows baseline and
adaptive
placement policies to be evaluated using a consistent workflow.

# Project Status

**Last updated:** 2026-09-20  
**Current phase:** Phases 1–20 complete. Python and Java simulations both executed.

## Environment

| Component | Status |
|-----------|--------|
| Python 3.13.7 | ML + Python simulation |
| JDK 17.0.12 | `C:\Program Files\Java\jdk-17` |
| Maven 3.9.16 | `apache-maven-3.9.16/` in the project folder (gitignored) |
| CloudSim Plus 8.5.7 | `org.cloudsimplus:cloudsimplus` — compiled and run |

Default `java` on PATH may still be 8. Always set `JAVA_HOME` to JDK 17 before Maven.

## Tests

- Python: 15 passed
- Java: 5 passed (`PlacementAndPowerTest`)

## Java how to run

```powershell
.\run_java_simulation.ps1
```

## Honest experimental note

Adaptive consolidation reduced energy vs First/Best Fit mainly by **powering down empty hosts**. RF prediction did **not** beat the no-prediction adaptive ablation on energy or migrations in the default config. Java and Python reported the same table.

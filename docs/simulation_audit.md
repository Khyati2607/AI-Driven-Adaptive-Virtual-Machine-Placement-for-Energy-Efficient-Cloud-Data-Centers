# Adaptive placement audit

This audit is against the observed run (First/Best Fit ~83635 Wh and 0 migrations; AdaptiveNoPrediction ~21185 Wh and 80 migrations) and the code in `AdaptiveRfPlacement` / `src/simulate_datacenter.py`.

## Answers

| # | Question | Finding |
|---|----------|---------|
| 1 | How often is `consolidateUnderloaded()` called? | **Once per simulation step**, after overload handling. Default 500 steps ⇒ 500 calls. Not once per VM. |
| 2 | Same VM multiple times in one interval? | **Blocked** by a `movedVms` set. A VM is assigned at most once per `rebalance`. |
| 3 | Host underloaded immediately after receiving VMs? | **Was possible as a destination chain**; receivers are **not** used as consolidation *sources* in the same interval (`receivedHosts`). Snapshot util is taken **before** moves. |
| 4 | Utilization recalculated after every migration? | **Live** dest util is used for dest feasibility. **Underload classification** uses the start-of-interval snapshot so a host is not re-labeled mid-interval. After overload moves, source live util is rechecked to stop further offloads. |
| 5 | Inactive hosts excluded? | **Yes** for dest and source (`h.active`). Empty hosts are powered down only if `vms.isEmpty()`. |
| 6 | Cooldown / hysteresis? | Cooldown existed on **consolidation only**; **overload path had no cooldown**. Hysteresis (`overload ± margin`) existed for overload trigger; dests could still be filled up to the overload line. |
| 7 | Same VM across consecutive intervals? | **Yes**, after cooldown elapsed. Combined with last-VM-to-any-idle-host, this produced extra consolidations (80 vs a one-shot pack). |
| 8 | Is every consolidation counted as a migration? | **Yes, by design.** Metrics count any VM host-id change between steps, including consolidation. That is a real migration cost, not a logging bug. |
| 9 | Does AdaptiveRF use Random Forest? | **Yes, if `usePrediction=true`.** Each step copies `Predicted_CPU` from `predictions.csv` (RF export) into `vm.predictedCpuPct`. Demand is `peCount * predicted/100`. |
| 10 | Are AdaptiveRF and AdaptiveNoPrediction different? | **Yes.** Same control flow; demand uses **predicted** vs **current** CPU. They are not guaranteed to produce different energy. |

## Root cause of repeated consolidations

Underload used **instantaneous CPU** (or “last VM may go anywhere”). Bitbrains VMs are often ~4% CPU, so almost every host stayed “underloaded”. After packing, small CPU differences made a host look “busier”, so VMs moved again after cooldown. Empty hosts then deactivated, then another host looked underloaded. That is **algorithmic thrashing**, not a display bug.

## Fixes (justified, not a migration cap)

- Cooldown on **overload and** consolidation.
- Dest must stay ≤ `overload - margin` (hysteresis).
- Consolidation dest must be **structurally denser** (more reserved PE) or **same density and lower host id** (one-way packing). Instantaneous CPU no longer chooses dest.
- One VM move per interval; receivers not consolidation sources the same interval.
- Inactive hosts never destinations.
- RF still wired through `effectiveDemandPe(usePrediction)`.

No target migration count is hard-coded.

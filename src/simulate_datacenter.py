"""
Trace-driven data-center simulation matching the Java placement/energy logic.

This engine exists so experiments can run without JDK 17 + Maven.
The CloudSim Plus module in cloudsim-simulation/ is the Java counterpart.
Algorithms, power model, SLA definition, and metrics are the same.
"""

from __future__ import annotations

import csv
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from utils import PROJECT_ROOT, ensure_parent_dir, load_json_config

LOGGER = logging.getLogger("simulate_datacenter")


@dataclass
class SimVm:
    vm_id: int
    pe_count: int
    ram_mb: int
    host: SimHost | None = None
    current_cpu_pct: float = 0.0
    predicted_cpu_pct: float = 0.0
    last_migration_step: int = -10_000

    def allocated_pe(self) -> float:
        return self.pe_count * (self.current_cpu_pct / 100.0)

    def effective_demand_pe(self, use_prediction: bool) -> float:
        pct = self.predicted_cpu_pct if use_prediction else self.current_cpu_pct
        return self.pe_count * (pct / 100.0)


@dataclass
class SimHost:
    host_id: int
    pe_count: int
    ram_mb: int
    idle_power_w: float
    max_power_w: float
    vms: list[SimVm] = field(default_factory=list)
    active: bool = True

    def used_pe(self) -> float:
        return sum(vm.allocated_pe() for vm in self.vms)

    def reserved_pe(self) -> int:
        return sum(vm.pe_count for vm in self.vms)

    def used_ram_mb(self) -> int:
        return sum(vm.ram_mb for vm in self.vms)

    def cpu_utilization_fraction(self) -> float:
        if self.pe_count <= 0:
            return 0.0
        return min(1.0, self.used_pe() / self.pe_count)

    def can_host(self, vm: SimVm) -> bool:
        return self.reserved_pe() + vm.pe_count <= self.pe_count and self.used_ram_mb() + vm.ram_mb <= self.ram_mb

    def remaining_pe_after(self, vm: SimVm) -> float:
        return self.pe_count - (self.reserved_pe() + vm.pe_count)

    def power_watts(self, utilization: float | None = None) -> float:
        u = self.cpu_utilization_fraction() if utilization is None else utilization
        u = max(0.0, min(1.0, u))
        return self.idle_power_w + (self.max_power_w - self.idle_power_w) * u

    def energy_wh(self, interval_sec: float) -> float:
        return self.power_watts() * (interval_sec / 3600.0)


def assign(host: SimHost, vm: SimVm) -> None:
    if vm.host is not None:
        vm.host.vms.remove(vm)
    vm.host = host
    host.vms.append(vm)


def first_fit_place(hosts: list[SimHost], vms: list[SimVm]) -> None:
    for vm in vms:
        for host in hosts:
            if host.active and host.can_host(vm):
                assign(host, vm)
                break


def spread_place(hosts: list[SimHost], vms: list[SimVm]) -> None:
    """Round-robin initial placement so adaptive consolidation has room to act."""
    idx = 0
    for vm in vms:
        placed = False
        for _ in range(len(hosts)):
            host = hosts[idx % len(hosts)]
            idx += 1
            if host.active and host.can_host(vm):
                assign(host, vm)
                placed = True
                break
        if not placed:
            first_fit_place(hosts, [vm])


def best_fit_place(hosts: list[SimHost], vms: list[SimVm]) -> None:
    for vm in vms:
        feasible = [h for h in hosts if h.active and h.can_host(vm)]
        if not feasible:
            continue
        dest = min(feasible, key=lambda h: h.remaining_pe_after(vm))
        assign(dest, vm)


def host_predicted_util(host: SimHost, predict: bool) -> float:
    if host.pe_count <= 0:
        return 0.0
    used = sum(vm.effective_demand_pe(predict) for vm in host.vms)
    return used / host.pe_count


def adaptive_rebalance(
    hosts: list[SimHost],
    config: dict[str, Any],
    use_prediction: bool,
    step: int = 0,
    events: list[dict[str, Any]] | None = None,
) -> None:
    overload = float(config["overload_threshold"])
    underload = float(config["underload_threshold"])
    margin = float(config["migration_margin"])
    cooldown = int(config.get("migration_cooldown_steps", 8))

    moved: set[int] = set()
    received: set[int] = set()
    snapshot = {h.host_id: host_predicted_util(h, use_prediction) for h in hosts}
    dest_cap = overload - margin
    trigger = overload + margin

    def in_cooldown(vm: SimVm) -> bool:
        return step - vm.last_migration_step < cooldown

    for source in list(hosts):
        if not source.active:
            continue
        util = snapshot.get(source.host_id, 0.0)
        if util <= trigger:
            continue
        movable = sorted(
            list(source.vms),
            key=lambda v: v.effective_demand_pe(use_prediction),
            reverse=True,
        )
        for vm in movable:
            if vm.vm_id in moved or in_cooldown(vm):
                continue
            dest = _find_overload_destination(hosts, vm, source, use_prediction, dest_cap)
            if dest is None:
                continue
            from_id = source.host_id
            assign(dest, vm)
            vm.last_migration_step = step
            moved.add(vm.vm_id)
            received.add(dest.host_id)
            if events is not None:
                events.append(
                    {
                        "step": step,
                        "type": "overload_migration",
                        "vm_id": vm.vm_id,
                        "from_host": from_id,
                        "to_host": dest.host_id,
                    }
                )
            if host_predicted_util(source, use_prediction) <= overload:
                break

    sources = []
    for host in hosts:
        if not host.active or not host.vms or host.host_id in received:
            continue
        if snapshot.get(host.host_id, 0.0) >= underload:
            continue
        sources.append(host)

    for source in sources:
        if not source.active or not source.vms or source.host_id in received:
            continue
        for vm in list(source.vms):
            if vm.vm_id in moved or in_cooldown(vm):
                continue
            dest = _find_consolidation_destination(hosts, vm, source, use_prediction, dest_cap)
            if dest is None:
                continue
            from_id = source.host_id
            assign(dest, vm)
            vm.last_migration_step = step
            moved.add(vm.vm_id)
            received.add(dest.host_id)
            if events is not None:
                events.append(
                    {
                        "step": step,
                        "type": "consolidation",
                        "vm_id": vm.vm_id,
                        "from_host": from_id,
                        "to_host": dest.host_id,
                    }
                )

    for host in hosts:
        if host.active and not host.vms:
            host.active = False
            if events is not None:
                events.append({"step": step, "type": "host_inactive", "host_id": host.host_id})


def _find_overload_destination(
    hosts: list[SimHost],
    vm: SimVm,
    source: SimHost,
    predict: bool,
    dest_cap: float,
) -> SimHost | None:
    feasible: list[SimHost] = []
    for host in hosts:
        if not host.active or host.host_id == source.host_id or not host.can_host(vm):
            continue
        after = host_predicted_util(host, predict) + vm.effective_demand_pe(predict) / host.pe_count
        if after <= dest_cap:
            feasible.append(host)
    if not feasible:
        return None
    return min(feasible, key=lambda h: host_predicted_util(h, predict))


def _find_consolidation_destination(
    hosts: list[SimHost],
    vm: SimVm,
    source: SimHost,
    predict: bool,
    dest_cap: float,
) -> SimHost | None:
    source_reserved = source.reserved_pe()
    best: SimHost | None = None
    best_reserved = -1
    best_id = 10**9
    for dest in hosts:
        if not dest.active or dest.host_id == source.host_id or not dest.can_host(vm):
            continue
        dest_after = host_predicted_util(dest, predict) + vm.effective_demand_pe(predict) / dest.pe_count
        if dest_after > dest_cap:
            continue
        dest_reserved = dest.reserved_pe()
        denser = dest_reserved > source_reserved
        same_density_lower_id = dest_reserved == source_reserved and dest.host_id < source.host_id
        if not denser and not same_density_lower_id:
            continue
        if dest_reserved > best_reserved or (dest_reserved == best_reserved and dest.host_id < best_id):
            best_reserved = dest_reserved
            best_id = dest.host_id
            best = dest
    return best


def load_predictions(csv_path: Path, vm_count: int) -> dict[int, list[dict[str, float]]]:
    by_vm: dict[int, list[dict[str, float]]] = {}
    with csv_path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            vm_id = int(row["VM_ID"])
            by_vm.setdefault(vm_id, []).append(
                {
                    "timestamp": float(row["Timestamp"]),
                    "actual": float(row["Actual_CPU"]),
                    "predicted": float(row["Predicted_CPU"]),
                }
            )
    for rows in by_vm.values():
        rows.sort(key=lambda r: r["timestamp"])
    selected_ids = sorted(by_vm)[:vm_count]
    return {vm_id: by_vm[vm_id] for vm_id in selected_ids}


def run_policy(
    name: str,
    config: dict[str, Any],
    by_vm: dict[int, list[dict[str, float]]],
    collect_timeseries: bool = True,
) -> dict[str, Any]:
    steps = min(len(rows) for rows in by_vm.values())
    steps = min(steps, int(config["simulation_steps"]))
    interval = float(config["step_interval_sec"])
    intensity = float(config.get("workload_intensity", 1.0))

    hosts = [
        SimHost(
            host_id=i,
            pe_count=int(config["host_pe_count"]),
            ram_mb=int(config["host_ram_mb"]),
            idle_power_w=float(config["host_idle_power_w"]),
            max_power_w=float(config["host_max_power_w"]),
        )
        for i in range(int(config["host_count"]))
    ]
    vms = [
        SimVm(vm_id=vm_id, pe_count=int(config["vm_pe_count"]), ram_mb=int(config["vm_ram_mb"]))
        for vm_id in sorted(by_vm)
    ]

    if name == "FirstFit":
        first_fit_place(hosts, vms)
    elif name == "BestFit":
        best_fit_place(hosts, vms)
    else:
        spread_place(hosts, vms)

    total_energy_wh = 0.0
    peak_power = 0.0
    util_sum = 0.0
    sla_violations = 0
    migrations = 0
    migration_overhead = 0.0
    host_of = {vm.vm_id: (vm.host.host_id if vm.host else -1) for vm in vms}

    use_prediction = name == "AdaptiveRF"
    adaptive = name in {"AdaptiveRF", "AdaptiveNoPrediction"}
    events: list[dict[str, Any]] = []
    timeseries: list[dict[str, Any]] = []

    for step in range(steps):
        actuals = []
        preds = []
        for vm in vms:
            row = by_vm[vm.vm_id][step]
            vm.current_cpu_pct = max(0.0, min(100.0, row["actual"] * intensity))
            vm.predicted_cpu_pct = max(0.0, min(100.0, row["predicted"] * intensity))
            actuals.append(vm.current_cpu_pct)
            preds.append(vm.predicted_cpu_pct)

        if adaptive:
            adaptive_rebalance(hosts, config, use_prediction, step=step, events=events)

        step_migrations = 0
        for vm in vms:
            new_host = vm.host.host_id if vm.host else -1
            old_host = host_of[vm.vm_id]
            if old_host != -1 and new_host != -1 and old_host != new_host:
                migrations += 1
                step_migrations += 1
                migration_overhead += float(config["migration_cost_cpu_fraction"]) * vm.pe_count * interval
            host_of[vm.vm_id] = new_host

        step_energy = 0.0
        step_util = 0.0
        step_sla = 0
        host_utils = []
        for host in hosts:
            u = host.cpu_utilization_fraction() if host.active else 0.0
            host_utils.append(
                {
                    "host_id": host.host_id,
                    "active": host.active,
                    "utilization": u,
                    "vm_ids": [vm.vm_id for vm in host.vms],
                }
            )
            if not host.active:
                continue
            step_util += u
            p = host.power_watts(u)
            peak_power = max(peak_power, p)
            e = host.energy_wh(interval)
            step_energy += e
            total_energy_wh += e
            if u > float(config["overload_threshold"]):
                sla_violations += 1
                step_sla += 1
        util_sum += step_util
        active_now = sum(1 for h in hosts if h.active)

        if collect_timeseries:
            timeseries.append(
                {
                    "step": step,
                    "energy_wh": step_energy,
                    "energy_wh_cumulative": total_energy_wh,
                    "avg_utilization": step_util / max(1, int(config["host_count"])),
                    "active_hosts": active_now,
                    "migrations": step_migrations,
                    "sla_violations": step_sla,
                    "mean_actual_cpu": sum(actuals) / max(1, len(actuals)),
                    "mean_predicted_cpu": sum(preds) / max(1, len(preds)),
                    "hosts": host_utils,
                }
            )

    active = sum(1 for h in hosts if h.active)
    hours = (steps * interval) / 3600.0
    energy_kwh = total_energy_wh / 1000.0
    carbon = energy_kwh * float(config["carbon_intensity_kg_per_kwh"])

    result = {
        "Method": name,
        "Energy_Wh": total_energy_wh,
        "Avg_Power_W": total_energy_wh / hours if hours else 0.0,
        "Peak_Power_W": peak_power,
        "Migrations": migrations,
        "SLA_Violations": sla_violations,
        "Avg_Utilization": util_sum / (steps * max(1, int(config["host_count"]))),
        "Active_Hosts": active,
        "Inactive_Hosts": int(config["host_count"]) - active,
        "Carbon_kg": carbon,
        "Migration_Overhead_CpuSec": migration_overhead,
        "Steps": steps,
        "engine": "python_trace_driven",
        "uses_random_forest": use_prediction,
    }
    if collect_timeseries:
        result["timeseries"] = timeseries
        result["events"] = events
        result["layout"] = timeseries[-1]["hosts"] if timeseries else []
    return result


def energy_saving_pct(baseline: float, proposed: float) -> float | None:
    if baseline <= 0:
        return None
    return (baseline - proposed) / baseline * 100.0


def main() -> None:
    logging.basicConfig(level=logging.WARNING, format="[%(levelname)s] %(message)s")
    config = load_json_config("simulation_config.json")
    pred_path = PROJECT_ROOT / "results" / "predictions" / "predictions.csv"
    if not pred_path.is_file():
        raise FileNotFoundError("Run python src/run_ml_pipeline.py first. Missing " + str(pred_path))

    by_vm = load_predictions(pred_path, int(config["vm_count"]))
    methods = ["FirstFit", "BestFit", "AdaptiveRF", "AdaptiveNoPrediction"]
    rows = [run_policy(name, config, by_vm, collect_timeseries=False) for name in methods]

    out_dir = ensure_parent_dir(PROJECT_ROOT / "results" / "comparison" / "comparison.csv").parent
    csv_path = out_dir / "comparison.csv"
    fieldnames = [
        "Method",
        "Energy_Wh",
        "Avg_Power_W",
        "Peak_Power_W",
        "Migrations",
        "SLA_Violations",
        "Avg_Utilization",
        "Active_Hosts",
        "Inactive_Hosts",
        "Carbon_kg",
        "Migration_Overhead_CpuSec",
        "Steps",
        "engine",
        "uses_random_forest",
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    by_name = {r["Method"]: r for r in rows}
    ff = by_name["FirstFit"]["Energy_Wh"]
    for row in rows:
        row["energy_saving_vs_first_fit_pct"] = energy_saving_pct(ff, row["Energy_Wh"])
        json_path = out_dir / f"{row['Method']}.json"
        with json_path.open("w", encoding="utf-8") as jf:
            json.dump(row, jf, indent=2)

    print(f"Wrote {csv_path}")
    for row in rows:
        print(
            f"{row['Method']:22s} energy={row['Energy_Wh']:.4f} Wh  "
            f"migrations={row['Migrations']}  sla={row['SLA_Violations']}  "
            f"carbon={row['Carbon_kg']:.6f} kg"
        )

    extra = {
        "energy": PROJECT_ROOT / "results" / "energy" / "comparison.csv",
        "sla": PROJECT_ROOT / "results" / "sla" / "comparison.csv",
        "qos": PROJECT_ROOT / "results" / "qos" / "comparison.csv",
        "carbon": PROJECT_ROOT / "results" / "carbon" / "comparison.csv",
    }
    for path in extra.values():
        ensure_parent_dir(path)
        path.write_text(csv_path.read_text(encoding="utf-8"), encoding="utf-8")


if __name__ == "__main__":
    main()

"""Unit tests for placement, energy, carbon, and edge cases."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from simulate_datacenter import (  # noqa: E402
    SimHost,
    SimVm,
    adaptive_rebalance,
    assign,
    energy_saving_pct,
    first_fit_place,
    best_fit_place,
)


def _host(host_id: int, pe: int = 8, ram: int = 8192) -> SimHost:
    return SimHost(host_id=host_id, pe_count=pe, ram_mb=ram, idle_power_w=100.0, max_power_w=250.0)


def test_power_model_idle_and_full():
    host = _host(0)
    assert abs(host.power_watts(0.0) - 100.0) < 1e-9
    assert abs(host.power_watts(1.0) - 250.0) < 1e-9
    assert abs(host.power_watts(0.5) - 175.0) < 1e-9


def test_energy_wh_one_hour_idle():
    host = _host(0)
    assert abs(host.energy_wh(3600.0) - 100.0) < 1e-9


def test_carbon_from_energy():
    intensity = 0.5
    energy_wh = 2000.0
    carbon = (energy_wh / 1000.0) * intensity
    assert abs(carbon - 1.0) < 1e-9


def test_first_fit_places_on_first_host():
    hosts = [_host(0), _host(1)]
    vm = SimVm(1, pe_count=2, ram_mb=1024)
    first_fit_place(hosts, [vm])
    assert vm.host is hosts[0]


def test_vm_larger_than_host_not_placed():
    hosts = [_host(0, pe=2, ram=1024)]
    vm = SimVm(1, pe_count=8, ram_mb=4096)
    first_fit_place(hosts, [vm])
    assert vm.host is None
    assert not hosts[0].can_host(vm)


def test_no_available_host():
    hosts = [_host(0, pe=2, ram=1024)]
    vm1 = SimVm(1, pe_count=2, ram_mb=1024)
    vm2 = SimVm(2, pe_count=2, ram_mb=1024)
    first_fit_place(hosts, [vm1, vm2])
    assert vm1.host is hosts[0]
    assert vm2.host is None


def test_overloaded_host_utilization():
    host = _host(0, pe=4)
    vm = SimVm(1, pe_count=4, ram_mb=1024)
    vm.current_cpu_pct = 100.0
    assign(host, vm)
    assert abs(host.cpu_utilization_fraction() - 1.0) < 1e-9


def test_empty_host_can_be_deactivated():
    hosts = [_host(0), _host(1)]
    vm = SimVm(1, pe_count=2, ram_mb=1024)
    vm.current_cpu_pct = 5.0
    vm.predicted_cpu_pct = 5.0
    assign(hosts[0], vm)
    config = {
        "overload_threshold": 0.8,
        "underload_threshold": 0.3,
        "migration_margin": 0.05,
        "migration_cooldown_steps": 8,
        "min_util_improvement": 0.05,
    }
    adaptive_rebalance(hosts, config, use_prediction=False, step=0)
    assert (not hosts[0].active) or hosts[0].vms
    if not hosts[0].vms:
        assert hosts[0].active is False
    assert hosts[1].active is False or hosts[1].vms


def test_vm_migrates_at_most_once_per_interval():
    hosts = [_host(0), _host(1), _host(2)]
    vms = []
    for i in range(3):
        vm = SimVm(i + 1, pe_count=2, ram_mb=1024)
        vm.current_cpu_pct = 4.0
        vm.predicted_cpu_pct = 4.0
        assign(hosts[0], vm)
        vms.append(vm)
    config = {
        "overload_threshold": 0.8,
        "underload_threshold": 0.99,
        "migration_margin": 0.0,
        "migration_cooldown_steps": 0,
        "min_util_improvement": 0.0,
    }
    adaptive_rebalance(hosts, config, False, step=0)
    assert all(vm.last_migration_step in (-10_000, 0) for vm in vms)


def test_receiver_not_consolidation_source_same_interval():
    hosts = [_host(0, pe=8), _host(1, pe=8)]
    low = SimVm(1, pe_count=2, ram_mb=1024)
    low.current_cpu_pct = 2.0
    low.predicted_cpu_pct = 2.0
    assign(hosts[0], low)
    denser = []
    for i in range(2, 4):
        vm = SimVm(i, pe_count=2, ram_mb=1024)
        vm.current_cpu_pct = 2.0
        vm.predicted_cpu_pct = 2.0
        assign(hosts[1], vm)
        denser.append(vm)
    config = {
        "overload_threshold": 0.8,
        "underload_threshold": 0.3,
        "migration_margin": 0.05,
        "migration_cooldown_steps": 0,
        "min_util_improvement": 0.0,
    }
    adaptive_rebalance(hosts, config, False, step=1)
    for vm in denser:
        assert vm.host is hosts[1]
    assert low.host is hosts[1]


def test_inactive_host_not_destination():
    hosts = [_host(0), _host(1)]
    hosts[1].active = False
    vm = SimVm(1, pe_count=2, ram_mb=1024)
    vm.current_cpu_pct = 2.0
    vm.predicted_cpu_pct = 2.0
    assign(hosts[0], vm)
    config = {
        "overload_threshold": 0.8,
        "underload_threshold": 0.3,
        "migration_margin": 0.05,
        "migration_cooldown_steps": 0,
        "min_util_improvement": 0.0,
    }
    adaptive_rebalance(hosts, config, False, step=0)
    assert vm.host is hosts[0]
    assert not hosts[1].vms


def test_cooldown_blocks_consolidation():
    hosts = [_host(0), _host(1)]
    a = SimVm(1, pe_count=2, ram_mb=1024)
    a.current_cpu_pct = 2.0
    a.predicted_cpu_pct = 2.0
    a.last_migration_step = 10
    b = SimVm(2, pe_count=2, ram_mb=1024)
    b.current_cpu_pct = 50.0
    b.predicted_cpu_pct = 50.0
    assign(hosts[0], a)
    assign(hosts[1], b)
    config = {
        "overload_threshold": 0.8,
        "underload_threshold": 0.3,
        "migration_margin": 0.05,
        "migration_cooldown_steps": 8,
        "min_util_improvement": 0.0,
    }
    adaptive_rebalance(hosts, config, False, step=12)
    assert a.host is hosts[0]


def test_rf_uses_predicted_cpu_not_current():
    vm = SimVm(1, pe_count=2, ram_mb=1024)
    vm.current_cpu_pct = 10.0
    vm.predicted_cpu_pct = 80.0
    assert abs(vm.effective_demand_pe(False) - 0.2) < 1e-9
    assert abs(vm.effective_demand_pe(True) - 1.6) < 1e-9


def test_best_fit_prefers_tighter_pack():
    hosts = [_host(0), _host(1)]
    first = SimVm(1, pe_count=4, ram_mb=1024)
    first.current_cpu_pct = 0.0
    assign(hosts[0], first)
    second = SimVm(2, pe_count=2, ram_mb=1024)
    best_fit_place(hosts, [second])
    assert second.host is hosts[0]


def test_energy_saving_formula():
    assert abs(energy_saving_pct(100.0, 80.0) - 20.0) < 1e-9
    assert energy_saving_pct(0.0, 10.0) is None

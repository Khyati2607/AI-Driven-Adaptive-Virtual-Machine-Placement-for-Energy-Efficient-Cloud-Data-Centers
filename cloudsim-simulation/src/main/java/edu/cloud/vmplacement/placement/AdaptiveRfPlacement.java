/**
 * Adaptive VM placement policy supporting two operating modes:
 *
 * 1. AdaptiveRF - uses Random Forest predicted CPU demand for placement decisions.
 * 2. AdaptiveNoPrediction - uses the current VM CPU demand without prediction.
 *
 * The policy handles overloaded hosts through VM migration and consolidates
 * underloaded hosts to reduce the number of active physical machines.
 * Migration cooldown and overload margins are used to reduce unnecessary
 * VM movement and avoid unstable placement decisions.
 */







package edu.cloud.vmplacement.placement;

import edu.cloud.vmplacement.config.SimulationConfig;
import edu.cloud.vmplacement.model.SimHost;
import edu.cloud.vmplacement.model.SimVm;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.logging.Logger;

/**
 * Adaptive placement using current CPU or Random Forest predicted CPU.
 *
 * Underload packing uses reserved PE / host id (structural), not instantaneous CPU,
 * so a temporary spike cannot reverse a consolidation. Overload uses demand
 * (predicted if enabled) with hysteresis and cooldown.
 */
public final class AdaptiveRfPlacement implements PlacementPolicy {

    private static final Logger LOG = Logger.getLogger(AdaptiveRfPlacement.class.getName());

    private final SimulationConfig config;
    private final boolean usePrediction;

    public AdaptiveRfPlacement(SimulationConfig config, boolean usePrediction) {
        this.config = config;
        this.usePrediction = usePrediction;
    }

    @Override
    public String name() {
        return usePrediction ? "AdaptiveRF" : "AdaptiveNoPrediction";
    }

    public boolean usesRandomForest() {
        return usePrediction;
    }

    @Override
    public void initialPlacement(List<SimHost> hosts, List<SimVm> vms) {
        int idx = 0;
        for (SimVm vm : vms) {
            boolean placed = false;
            for (int n = 0; n < hosts.size(); n++) {
                SimHost host = hosts.get(idx % hosts.size());
                idx++;
                if (host.active && host.canHost(vm)) {
                    FirstFitPlacement.assign(host, vm);
                    placed = true;
                    break;
                }
            }
            if (!placed) {
                new FirstFitPlacement().initialPlacement(hosts, List.of(vm));
            }
        }
    }

    @Override
    public void rebalance(List<SimHost> hosts, List<SimVm> vms, boolean usePredictionFlag) {
        rebalance(hosts, vms, usePredictionFlag, 0);
    }

    @Override
    public void rebalance(List<SimHost> hosts, List<SimVm> vms, boolean usePredictionFlag, int step) {
        boolean predict = usePrediction && usePredictionFlag;
        Set<Integer> movedVms = new HashSet<>();
        Set<Integer> receivedHosts = new HashSet<>();
        Map<Integer, Double> snapshot = new HashMap<>();
        for (SimHost host : hosts) {
            snapshot.put(host.id, hostDemandUtil(host, predict));
        }
        migrateFromOverloaded(hosts, predict, step, movedVms, receivedHosts, snapshot);
        consolidateUnderloaded(hosts, predict, step, movedVms, receivedHosts, snapshot);
        deactivateEmptyHosts(hosts);
    }

    private double hostDemandUtil(SimHost host, boolean predict) {
        double used = host.vms.stream().mapToDouble(v -> v.effectiveDemandPe(predict)).sum();
        return host.peCount == 0 ? 0 : used / host.peCount;
    }

    private boolean inCooldown(SimVm vm, int step) {
        return step - vm.lastMigrationStep < config.migrationCooldownSteps;
    }

    private void migrateFromOverloaded(
            List<SimHost> hosts,
            boolean predict,
            int step,
            Set<Integer> movedVms,
            Set<Integer> receivedHosts,
            Map<Integer, Double> snapshot
    ) {
        double trigger = config.overloadThreshold + config.migrationMargin;
        for (SimHost source : new ArrayList<>(hosts)) {
            if (!source.active) {
                continue;
            }
            double util = snapshot.getOrDefault(source.id, 0.0);
            if (util <= trigger) {
                continue;
            }
            List<SimVm> movable = new ArrayList<>(source.vms);
            movable.sort(Comparator.comparingDouble((SimVm v) -> v.effectiveDemandPe(predict)).reversed());
            for (SimVm vm : movable) {
                if (movedVms.contains(vm.id) || inCooldown(vm, step)) {
                    continue;
                }
                SimHost dest = findOverloadDestination(hosts, vm, source, predict);
                if (dest == null) {
                    continue;
                }
                LOG.fine(() -> String.format(
                        "Overload migrate VM %d Host %d -> Host %d",
                        vm.id, source.id, dest.id));
                FirstFitPlacement.assign(dest, vm);
                vm.lastMigrationStep = step;
                movedVms.add(vm.id);
                receivedHosts.add(dest.id);
                if (hostDemandUtil(source, predict) <= config.overloadThreshold) {
                    break;
                }
            }
        }
    }

    private SimHost findOverloadDestination(List<SimHost> hosts, SimVm vm, SimHost source, boolean predict) {
        double destCap = config.overloadThreshold - config.migrationMargin;
        return hosts.stream()
                .filter(h -> h.active && h.id != source.id && h.canHost(vm))
                .filter(h -> hostDemandUtil(h, predict) + vm.effectiveDemandPe(predict) / h.peCount <= destCap)
                .min(Comparator.comparingDouble(h -> hostDemandUtil(h, predict)))
                .orElse(null);
    }

    private void consolidateUnderloaded(
            List<SimHost> hosts,
            boolean predict,
            int step,
            Set<Integer> movedVms,
            Set<Integer> receivedHosts,
            Map<Integer, Double> snapshot
    ) {
        List<SimHost> sources = new ArrayList<>();
        for (SimHost host : hosts) {
            if (!host.active || host.vms.isEmpty() || receivedHosts.contains(host.id)) {
                continue;
            }
            if (snapshot.getOrDefault(host.id, 0.0) >= config.underloadThreshold) {
                continue;
            }
            sources.add(host);
        }

        for (SimHost source : sources) {
            if (!source.active || source.vms.isEmpty() || receivedHosts.contains(source.id)) {
                continue;
            }
            for (SimVm vm : new ArrayList<>(source.vms)) {
                if (movedVms.contains(vm.id) || inCooldown(vm, step)) {
                    continue;
                }
                SimHost dest = findConsolidationDestination(hosts, vm, source, predict);
                if (dest == null) {
                    continue;
                }
                LOG.fine(() -> String.format("Consolidate VM %d Host %d -> Host %d", vm.id, source.id, dest.id));
                FirstFitPlacement.assign(dest, vm);
                vm.lastMigrationStep = step;
                movedVms.add(vm.id);
                receivedHosts.add(dest.id);
            }
        }
    }

    /**
     * Pack onto a strictly denser active host, or onto a lower host-id when density is equal
     * (one-way packing). Instantaneous CPU is not used to pick dest, which prevents spike-driven
     * ping-pong. Demand is still used to reject dests that would exceed overload-margin.
     */
    private SimHost findConsolidationDestination(List<SimHost> hosts, SimVm vm, SimHost source, boolean predict) {
        int sourceReserved = source.reservedPe();
        double destCap = config.overloadThreshold - config.migrationMargin;
        SimHost best = null;
        int bestReserved = -1;
        int bestId = Integer.MAX_VALUE;
        for (SimHost dest : hosts) {
            if (!dest.active || dest.id == source.id || !dest.canHost(vm)) {
                continue;
            }
            double destAfter = hostDemandUtil(dest, predict) + vm.effectiveDemandPe(predict) / dest.peCount;
            if (destAfter > destCap) {
                continue;
            }
            int destReserved = dest.reservedPe();
            boolean denser = destReserved > sourceReserved;
            boolean sameDensityLowerId = destReserved == sourceReserved && dest.id < source.id;
            if (!denser && !sameDensityLowerId) {
                continue;
            }
            if (destAfter - hostDemandUtil(dest, predict) < 0 && !denser) {
                continue;
            }
            if (destReserved > bestReserved || (destReserved == bestReserved && dest.id < bestId)) {
                bestReserved = destReserved;
                bestId = dest.id;
                best = dest;
            }
        }
        return best;
    }

    private void deactivateEmptyHosts(List<SimHost> hosts) {
        for (SimHost host : hosts) {
            if (host.active && host.vms.isEmpty()) {
                host.active = false;
                LOG.fine(() -> "Host " + host.id + " became inactive");
            }
        }
    }
}

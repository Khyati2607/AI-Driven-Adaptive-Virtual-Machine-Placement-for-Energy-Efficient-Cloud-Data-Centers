/**
 * Executes the trace-driven VM placement simulation.
 *
 * Workload traces are processed over simulation intervals while
 * the selected placement policy performs VM placement and
 * rebalancing. Performance metrics are collected for comparison.
 */

package edu.cloud.vmplacement.simulation;

import edu.cloud.vmplacement.config.SimulationConfig;
import edu.cloud.vmplacement.metrics.SimulationMetrics;
import edu.cloud.vmplacement.model.SimHost;
import edu.cloud.vmplacement.model.SimVm;
import edu.cloud.vmplacement.placement.AdaptiveRfPlacement;
import edu.cloud.vmplacement.placement.BestFitPlacement;
import edu.cloud.vmplacement.placement.FirstFitPlacement;
import edu.cloud.vmplacement.placement.PlacementPolicy;
import edu.cloud.vmplacement.trace.PredictionTraceLoader;
import edu.cloud.vmplacement.trace.PredictionTraceLoader.TraceRow;
import edu.cloud.vmplacement.power.LinearPowerModel;

import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.logging.Level;
import java.util.logging.Logger;

public final class TraceDrivenSimulation {

    private static final Logger LOG = Logger.getLogger(TraceDrivenSimulation.class.getName());

    private final SimulationConfig config;

    public TraceDrivenSimulation(SimulationConfig config) {
        this.config = config;
    }

    public SimulationMetrics run(PlacementPolicy policy, Path predictionsCsv) throws Exception {
        Map<Integer, List<TraceRow>> byVm = PredictionTraceLoader.loadByVm(predictionsCsv, config.vmCount);
        if (byVm.isEmpty()) {
            throw new IllegalStateException("No prediction rows loaded from " + predictionsCsv);
        }

        List<Integer> vmIds = byVm.keySet().stream().sorted().limit(config.vmCount).toList();
        int steps = PredictionTraceLoader.commonStepCount(byVm, config.simulationSteps);

        LinearPowerModel powerModel = new LinearPowerModel(config.hostIdlePowerW, config.hostMaxPowerW);
        List<SimHost> hosts = new ArrayList<>();
        for (int i = 0; i < config.hostCount; i++) {
            hosts.add(new SimHost(i, config.hostPeCount, config.hostRamMb, config.hostBwMbps, powerModel));
        }

        List<SimVm> vms = new ArrayList<>();
        for (int vmId : vmIds) {
            vms.add(new SimVm(vmId, config.vmPeCount, config.vmRamMb));
        }

        policy.initialPlacement(hosts, vms);

        double totalEnergyWh = 0;
        double peakPower = 0;
        double utilSum = 0;
        int slaViolations = 0;
        int migrations = 0;
        double migrationOverhead = 0;

        int[] hostOf = new int[vms.size()];
        for (int i = 0; i < vms.size(); i++) {
            hostOf[i] = vms.get(i).host != null ? vms.get(i).host.id : -1;
        }

        for (int step = 0; step < steps; step++) {
            for (SimVm vm : vms) {
                TraceRow row = byVm.get(vm.id).get(step);
                vm.currentCpuPct = row.actualCpuPct();
                vm.predictedCpuPct = row.predictedCpuPct();
            }

            if (policy instanceof AdaptiveRfPlacement adaptive) {
                adaptive.rebalance(hosts, vms, adaptive.name().equals("AdaptiveRF"), step);
            }

            for (int i = 0; i < vms.size(); i++) {
                SimVm vm = vms.get(i);
                int newHost = vm.host != null ? vm.host.id : -1;
                if (hostOf[i] != -1 && newHost != -1 && hostOf[i] != newHost) {
                    migrations++;
                    migrationOverhead += config.migrationCostCpuFraction * vm.peCount * config.stepIntervalSec;
                }
                hostOf[i] = newHost;
            }

            for (SimHost host : hosts) {
                if (!host.active) {
                    continue;
                }
                double u = host.cpuUtilizationFraction();
                utilSum += u;
                double p = host.powerModel.powerWatts(u);
                peakPower = Math.max(peakPower, p);
                totalEnergyWh += host.powerModel.energyWh(u, config.stepIntervalSec);
                if (u > config.overloadThreshold) {
                    slaViolations++;
                }
            }
        }

        int active = (int) hosts.stream().filter(h -> h.active).count();
        SimulationMetrics m = new SimulationMetrics();
        m.method = policy.name();
        m.totalEnergyWh = totalEnergyWh;
        m.averagePowerW = totalEnergyWh / ((steps * config.stepIntervalSec) / 3600.0);
        m.peakPowerW = peakPower;
        m.migrations = migrations;
        m.slaViolations = slaViolations;
        m.avgHostUtilization = utilSum / (steps * Math.max(1, config.hostCount));
        m.activeHostsEnd = active;
        m.inactiveHostsEnd = config.hostCount - active;
        m.carbonKg = (totalEnergyWh / 1000.0) * config.carbonIntensityKgPerKwh;
        m.migrationOverheadCpuSec = migrationOverhead;
        m.simulationSteps = steps;

        LOG.log(Level.INFO, () -> m.method + " energyWh=" + m.totalEnergyWh + " migrations=" + m.migrations);
        return m;
    }
}

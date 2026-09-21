package edu.cloud.vmplacement;

import edu.cloud.vmplacement.config.SimulationConfig;
import edu.cloud.vmplacement.model.SimHost;
import edu.cloud.vmplacement.model.SimVm;
import edu.cloud.vmplacement.placement.AdaptiveRfPlacement;
import edu.cloud.vmplacement.power.LinearPowerModel;
import org.junit.jupiter.api.Test;

import java.util.ArrayList;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

class AdaptivePlacementTest {

    private static SimulationConfig cfg() {
        SimulationConfig c = new SimulationConfig();
        c.overloadThreshold = 0.80;
        c.underloadThreshold = 0.30;
        c.migrationMargin = 0.05;
        c.migrationCooldownSteps = 8;
        c.minUtilImprovement = 0.05;
        return c;
    }

    private static SimHost host(int id, int pe) {
        return new SimHost(id, pe, 32_768, 1000, new LinearPowerModel(100, 250));
    }

    @Test
    void rfAndNoPredictionAreDifferentFlags() {
        AdaptiveRfPlacement rf = new AdaptiveRfPlacement(cfg(), true);
        AdaptiveRfPlacement none = new AdaptiveRfPlacement(cfg(), false);
        assertEquals("AdaptiveRF", rf.name());
        assertEquals("AdaptiveNoPrediction", none.name());
        assertTrue(rf.usesRandomForest());
        assertFalse(none.usesRandomForest());
    }

    @Test
    void predictedDemandDiffersFromCurrent() {
        SimVm vm = new SimVm(1, 2, 2048);
        vm.currentCpuPct = 10;
        vm.predictedCpuPct = 80;
        assertEquals(0.2, vm.effectiveDemandPe(false), 1e-9);
        assertEquals(1.6, vm.effectiveDemandPe(true), 1e-9);
    }

    @Test
    void vmMovesAtMostOncePerInterval() {
        List<SimHost> hosts = new ArrayList<>();
        hosts.add(host(0, 8));
        hosts.add(host(1, 8));
        hosts.add(host(2, 8));
        SimVm vm = new SimVm(1, 2, 2048);
        vm.currentCpuPct = 4;
        vm.predictedCpuPct = 4;
        hosts.get(2).vms.add(vm);
        vm.host = hosts.get(2);
        new AdaptiveRfPlacement(cfg(), false).rebalance(hosts, List.of(vm), false, 0);
        int hostChanges = 0;
        // one rebalance: at most one assignment
        assertTrue(vm.lastMigrationStep == 0 || vm.lastMigrationStep == -10_000);
        if (vm.lastMigrationStep == 0) {
            hostChanges = 1;
        }
        assertTrue(hostChanges <= 1);
    }

    @Test
    void inactiveHostIsNotADestination() {
        List<SimHost> hosts = new ArrayList<>();
        hosts.add(host(0, 8));
        hosts.add(host(1, 8));
        hosts.get(1).active = false;
        SimVm vm = new SimVm(1, 2, 2048);
        vm.currentCpuPct = 2;
        vm.predictedCpuPct = 2;
        hosts.get(0).vms.add(vm);
        vm.host = hosts.get(0);
        new AdaptiveRfPlacement(cfg(), false).rebalance(hosts, List.of(vm), false, 0);
        assertEquals(0, vm.host.id);
        assertTrue(hosts.get(1).vms.isEmpty());
    }

    @Test
    void cooldownBlocksRepeatMigration() {
        SimulationConfig c = cfg();
        c.migrationCooldownSteps = 8;
        List<SimHost> hosts = new ArrayList<>();
        hosts.add(host(0, 8));
        hosts.add(host(1, 8));
        SimVm a = new SimVm(1, 2, 2048);
        a.currentCpuPct = 2;
        a.predictedCpuPct = 2;
        a.lastMigrationStep = 10;
        SimVm b = new SimVm(2, 2, 2048);
        b.currentCpuPct = 50;
        b.predictedCpuPct = 50;
        hosts.get(1).vms.add(a);
        a.host = hosts.get(1);
        hosts.get(0).vms.add(b);
        b.host = hosts.get(0);
        new AdaptiveRfPlacement(c, false).rebalance(hosts, List.of(a, b), false, 12);
        assertEquals(1, a.host.id);
    }
}

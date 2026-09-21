package edu.cloud.vmplacement;

import edu.cloud.vmplacement.config.SimulationConfig;
import edu.cloud.vmplacement.model.SimHost;
import edu.cloud.vmplacement.model.SimVm;
import edu.cloud.vmplacement.placement.BestFitPlacement;
import edu.cloud.vmplacement.placement.FirstFitPlacement;
import edu.cloud.vmplacement.power.LinearPowerModel;
import org.junit.jupiter.api.Test;

import java.util.ArrayList;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

class PlacementAndPowerTest {

    @Test
    void linearPowerAtIdleAndFull() {
        LinearPowerModel p = new LinearPowerModel(100, 250);
        assertEquals(100, p.powerWatts(0), 1e-6);
        assertEquals(250, p.powerWatts(1), 1e-6);
        assertEquals(175, p.powerWatts(0.5), 1e-6);
    }

    @Test
    void firstFitPlacesVmOnFirstHost() {
        LinearPowerModel pm = new LinearPowerModel(100, 200);
        List<SimHost> hosts = List.of(new SimHost(0, 8, 8192, 1000, pm));
        SimVm vm = new SimVm(1, 2, 1024);
        new FirstFitPlacement().initialPlacement(new ArrayList<>(hosts), List.of(vm));
        assertNotNull(vm.host);
        assertEquals(0, vm.host.id);
    }

    @Test
    void overloadedHostDetected() {
        LinearPowerModel pm = new LinearPowerModel(100, 200);
        SimHost host = new SimHost(0, 4, 8192, 1000, pm);
        SimVm vm = new SimVm(1, 4, 1024);
        vm.currentCpuPct = 100;
        host.vms.add(vm);
        vm.host = host;
        assertEquals(1.0, host.cpuUtilizationFraction(), 1e-6);
    }

    @Test
    void vmTooLargeForHost() {
        LinearPowerModel pm = new LinearPowerModel(100, 200);
        SimHost host = new SimHost(0, 2, 1024, 1000, pm);
        SimVm vm = new SimVm(1, 4, 2048);
        assertFalse(host.canHost(vm));
    }

    @Test
    void bestFitPacksTighter() {
        LinearPowerModel pm = new LinearPowerModel(100, 200);
        List<SimHost> hosts = new ArrayList<>();
        hosts.add(new SimHost(0, 8, 16384, 1000, pm));
        hosts.add(new SimHost(1, 8, 16384, 1000, pm));
        SimVm vm = new SimVm(1, 2, 1024);
        new BestFitPlacement().initialPlacement(hosts, List.of(vm));
        assertNotNull(vm.host);
    }
}

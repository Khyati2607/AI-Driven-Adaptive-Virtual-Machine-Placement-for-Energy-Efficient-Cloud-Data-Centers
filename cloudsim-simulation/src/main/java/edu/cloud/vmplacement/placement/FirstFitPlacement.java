package edu.cloud.vmplacement.placement;

import edu.cloud.vmplacement.model.SimHost;
import edu.cloud.vmplacement.model.SimVm;

import java.util.List;
import java.util.Optional;


public final class FirstFitPlacement implements PlacementPolicy {

    @Override
    public String name() {
        return "FirstFit";
    }
/**
 * First Fit baseline for VM placement.
 *
 * Each VM is assigned to the first active host that has sufficient
 * processing elements (PE) and RAM. The policy performs only the
 * initial placement and does not perform dynamic VM migration or
 * consolidation during simulation.
 */

    @Override
    public void initialPlacement(List<SimHost> hosts, List<SimVm> vms) {
        for (SimVm vm : vms) {
            Optional<SimHost> host = hosts.stream().filter(h -> h.active && h.canHost(vm)).findFirst();
            host.ifPresent(h -> assign(h, vm));
        }
    }

    @Override
    public void rebalance(List<SimHost> hosts, List<SimVm> vms, boolean usePrediction) {
        // Static baseline: no migration after initial placement
    }

    static void assign(SimHost host, SimVm vm) {
        if (vm.host != null) {
            vm.host.vms.remove(vm);
        }
        vm.host = host;
        host.vms.add(vm);
    }
}

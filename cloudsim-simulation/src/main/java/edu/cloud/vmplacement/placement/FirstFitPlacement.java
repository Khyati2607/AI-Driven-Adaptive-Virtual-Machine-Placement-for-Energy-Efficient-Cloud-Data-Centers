package edu.cloud.vmplacement.placement;

import edu.cloud.vmplacement.model.SimHost;
import edu.cloud.vmplacement.model.SimVm;

import java.util.List;
import java.util.Optional;

/**
 * First Fit: place each VM on the first active host with enough PE and RAM.
 */
public final class FirstFitPlacement implements PlacementPolicy {

    @Override
    public String name() {
        return "FirstFit";
    }

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

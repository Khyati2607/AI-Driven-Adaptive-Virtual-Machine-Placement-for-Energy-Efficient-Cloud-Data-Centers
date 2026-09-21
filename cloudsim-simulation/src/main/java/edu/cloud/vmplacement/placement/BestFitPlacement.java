package edu.cloud.vmplacement.placement;
/**
 * Best Fit baseline for VM placement.
 *
 * Each VM is assigned to the feasible active host that leaves the
 * smallest remaining processing-element (PE) capacity after placement.
 * This static baseline performs initial placement without dynamic
 * migration or host consolidation.
 */

import edu.cloud.vmplacement.model.SimHost;
import edu.cloud.vmplacement.model.SimVm;

import java.util.Comparator;
import java.util.List;
import java.util.Optional;

public final class BestFitPlacement implements PlacementPolicy {

    @Override
    public String name() {
        return "BestFit";
    }

    @Override
    public void initialPlacement(List<SimHost> hosts, List<SimVm> vms) {
        for (SimVm vm : vms) {
            Optional<SimHost> best = hosts.stream()
                    .filter(h -> h.active && h.canHost(vm))
                    .min(Comparator.comparingDouble(h -> h.remainingPeAfter(vm)));
            best.ifPresent(h -> FirstFitPlacement.assign(h, vm));
        }
    }

    @Override
    public void rebalance(List<SimHost> hosts, List<SimVm> vms, boolean usePrediction) {
        // Static baseline
    }
}

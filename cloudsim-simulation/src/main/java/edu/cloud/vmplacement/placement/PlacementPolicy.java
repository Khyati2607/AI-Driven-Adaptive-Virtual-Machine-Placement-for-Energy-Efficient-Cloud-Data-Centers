package edu.cloud.vmplacement.placement;

import edu.cloud.vmplacement.model.SimHost;
import edu.cloud.vmplacement.model.SimVm;

import java.util.List;
import java.util.Optional;

public interface PlacementPolicy {
    String name();

    /** Initial placement of all VMs on empty hosts. */
    void initialPlacement(List<SimHost> hosts, List<SimVm> vms);

    /** Periodic rebalancing (migrations). */
    void rebalance(List<SimHost> hosts, List<SimVm> vms, boolean usePrediction);

    default void rebalance(List<SimHost> hosts, List<SimVm> vms, boolean usePrediction, int step) {
        rebalance(hosts, vms, usePrediction);
    }
}

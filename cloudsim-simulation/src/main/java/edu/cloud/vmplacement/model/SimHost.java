/**
 * Represents a physical host in the VM placement simulation.
 *
 * A simulated host maintains its resource capacity, current VM
 * allocation, active state, and resource utilization information.
 * These properties are used by placement policies to make hosting
 * and consolidation decisions.
 */

package edu.cloud.vmplacement.model;

import edu.cloud.vmplacement.power.LinearPowerModel;

import java.util.ArrayList;
import java.util.List;

public final class SimHost {

    public final int id;
    public final int peCount;
    public final long ramMb;
    public final long bwMbps;
    public final LinearPowerModel powerModel;
    public final List<SimVm> vms = new ArrayList<>();
    public boolean active = true;

    public SimHost(int id, int peCount, long ramMb, long bwMbps, LinearPowerModel powerModel) {
        this.id = id;
        this.peCount = peCount;
        this.ramMb = ramMb;
        this.bwMbps = bwMbps;
        this.powerModel = powerModel;
    }

    public double usedPe() {
        return vms.stream().mapToDouble(SimVm::allocatedPe).sum();
    }

    public int reservedPe() {
        return vms.stream().mapToInt(v -> v.peCount).sum();
    }

    public long usedRamMb() {
        return vms.stream().mapToLong(v -> v.ramMb).sum();
    }

    public double cpuUtilizationFraction() {
        if (peCount <= 0) {
            return 0;
        }
        return Math.min(1.0, usedPe() / peCount);
    }

    public boolean canHost(SimVm vm) {
        return reservedPe() + vm.peCount <= peCount && usedRamMb() + vm.ramMb <= ramMb;
    }

    /** Remaining reserved PE after placement (for Best Fit). */
    public double remainingPeAfter(SimVm vm) {
        return peCount - (reservedPe() + vm.peCount);
    }
}

/**
 * Linear power consumption model for simulated physical hosts.
 *
 * Power consumption is estimated from host utilization between
 * idle and maximum power levels. This model is used to compare
 * the energy impact of different VM placement strategies.
 */

package edu.cloud.vmplacement.power;

/**
 * Simplified host power model: P(u) = P_idle + (P_max - P_idle) * u, u in [0,1].
 * Energy (Wh) = Power (W) * time (h).
 */
public final class LinearPowerModel {

    private final double idlePowerW;
    private final double maxPowerW;

    public LinearPowerModel(double idlePowerW, double maxPowerW) {
        if (idlePowerW < 0 || maxPowerW < idlePowerW) {
            throw new IllegalArgumentException("Invalid power parameters");
        }
        this.idlePowerW = idlePowerW;
        this.maxPowerW = maxPowerW;
    }

    public double powerWatts(double cpuUtilizationFraction) {
        double u = Math.max(0.0, Math.min(1.0, cpuUtilizationFraction));
        return idlePowerW + (maxPowerW - idlePowerW) * u;
    }

    /** Energy in watt-hours for interval seconds at utilization u. */
    public double energyWh(double cpuUtilizationFraction, double intervalSec) {
        return powerWatts(cpuUtilizationFraction) * (intervalSec / 3600.0);
    }
}

package edu.cloud.vmplacement.simulation;

import org.cloudsimplus.core.CloudSimPlus;

/**
 * Initializes CloudSim Plus before trace-driven experiments.
 * Placement over Bitbrains prediction traces is implemented in TraceDrivenSimulation
 * so overload/underload/hysteresis stay explicit for the viva.
 */
public final class CloudSimBootstrap {

    private CloudSimBootstrap() {}

    public static CloudSimPlus start() {
        CloudSimPlus simulation = new CloudSimPlus();
        simulation.terminateAt(86400);
        return simulation;
    }
}

/**
 * Provides the basic CloudSim Plus simulation environment.
 *
 * This component initializes the simulation infrastructure required
 * to create and execute the virtualized data center experiment.
 */


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

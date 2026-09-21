/**
 * Central configuration for the CloudSim VM placement experiments.
 *
 * This class stores simulation parameters such as host resources,
 * VM resources, workload settings, placement policy options, and
 * experiment controls so that simulations can be reproduced consistently.
 */

package edu.cloud.vmplacement.config;

import com.google.gson.FieldNamingPolicy;
import com.google.gson.Gson;
import com.google.gson.GsonBuilder;

import java.io.IOException;
import java.io.Reader;
import java.nio.file.Files;
import java.nio.file.Path;

/**
 * Loads simulation parameters from JSON (see config/simulation_config.json at repo root).
 */
public class SimulationConfig {

    public int hostCount = 20;
    public int vmCount = 20;
    public int hostPeCount = 8;
    public long hostMips = 10_000;
    public long hostRamMb = 32_768;
    public long hostBwMbps = 10_000;
    public long hostStorageMb = 1_000_000;
    public double hostIdlePowerW = 100.0;
    public double hostMaxPowerW = 250.0;
    public int vmPeCount = 2;
    public long vmMips = 2_500;
    public long vmRamMb = 2_048;
    public long vmBwMbps = 1_000;
    public long vmStorageMb = 10_000;
    public double overloadThreshold = 0.80;
    public double underloadThreshold = 0.30;
    public double migrationMargin = 0.05;
    public double minUtilImprovement = 0.05;
    public int migrationCooldownSteps = 8;
    public double migrationCostCpuFraction = 0.10;
    public int simulationSteps = 500;
    public double stepIntervalSec = 300.0;
    public double carbonIntensityKgPerKwh = 0.5;
    public String predictionsCsv = "../results/predictions/predictions.csv";
    public String resultsDir = "../results/comparison";
    public String logLevel = "WARNING";

    public static SimulationConfig load(Path path) throws IOException {
        Gson gson = new GsonBuilder()
                .setFieldNamingPolicy(FieldNamingPolicy.LOWER_CASE_WITH_UNDERSCORES)
                .create();
        try (Reader reader = Files.newBufferedReader(path)) {
            return gson.fromJson(reader, SimulationConfig.class);
        }
    }
}

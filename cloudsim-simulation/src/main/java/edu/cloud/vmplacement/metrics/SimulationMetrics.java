/**
 * Stores performance metrics collected during VM placement simulation.
 *
 * The metrics support comparison of placement policies using energy
 * consumption, CPU utilization, SLA violations, VM migrations, and
 * simulation execution time.
 */



package edu.cloud.vmplacement.metrics;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;

public final class SimulationMetrics {

    public String method;
    public double totalEnergyWh;
    public double averagePowerW;
    public double peakPowerW;
    public int migrations;
    public int slaViolations;
    public double avgHostUtilization;
    public int activeHostsEnd;
    public int inactiveHostsEnd;
    public double carbonKg;
    public double migrationOverheadCpuSec;
    public long simulationSteps;

    public void saveJson(Path path) throws IOException {
        Files.createDirectories(path.getParent());
        Gson gson = new GsonBuilder().setPrettyPrinting().create();
        Files.writeString(path, gson.toJson(this));
    }

    public static String csvHeader() {
        return "Method,Energy_Wh,Avg_Power_W,Peak_Power_W,Migrations,SLA_Violations,Avg_Utilization,Active_Hosts,Inactive_Hosts,Carbon_kg,Migration_Overhead_CpuSec,Steps";
    }

    public String toCsvRow() {
        return String.format(
                "%s,%.6f,%.6f,%.6f,%d,%d,%.6f,%d,%d,%.6f,%.6f,%d",
                method,
                totalEnergyWh,
                averagePowerW,
                peakPowerW,
                migrations,
                slaViolations,
                avgHostUtilization,
                activeHostsEnd,
                inactiveHostsEnd,
                carbonKg,
                migrationOverheadCpuSec,
                simulationSteps);
    }
}

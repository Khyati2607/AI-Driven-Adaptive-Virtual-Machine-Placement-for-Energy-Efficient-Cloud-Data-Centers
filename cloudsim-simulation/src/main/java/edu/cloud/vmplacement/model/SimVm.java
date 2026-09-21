package edu.cloud.vmplacement.model;

public final class SimVm {

    public final int id;
    public final int peCount;
    public final long ramMb;
    public SimHost host;
    public double currentCpuPct;
    public double predictedCpuPct;
    public int lastMigrationStep = -10_000;

    public SimVm(int id, int peCount, long ramMb) {
        this.id = id;
        this.peCount = peCount;
        this.ramMb = ramMb;
    }

    public double allocatedPe() {
        return peCount * (currentCpuPct / 100.0);
    }

    public double effectiveDemandPe(boolean usePrediction) {
        double pct = usePrediction ? predictedCpuPct : currentCpuPct;
        return peCount * (pct / 100.0);
    }
}

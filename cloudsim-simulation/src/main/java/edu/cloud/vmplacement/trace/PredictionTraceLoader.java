package edu.cloud.vmplacement.trace;

import java.io.BufferedReader;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Loads Python-exported predictions.csv: VM_ID, Timestamp, Actual_CPU, Predicted_CPU, ...
 */
public final class PredictionTraceLoader {

    public record TraceRow(
            int vmId,
            long timestamp,
            double actualCpuPct,
            double predictedCpuPct,
            double memoryKb,
            int cpuCores
    ) {}

    public static Map<Integer, List<TraceRow>> loadByVm(Path csvPath, int maxVms) throws IOException {
        Map<Integer, List<TraceRow>> byVm = new HashMap<>();
        try (BufferedReader br = Files.newBufferedReader(csvPath)) {
            String header = br.readLine();
            if (header == null) {
                throw new IOException("Empty predictions file");
            }
            String line;
            while ((line = br.readLine()) != null) {
                String[] p = line.split(",", -1);
                if (p.length < 5) {
                    continue;
                }
                int vmId = Integer.parseInt(p[0].trim());
                if (maxVms > 0 && vmId > maxVms) {
                    continue;
                }
                long ts = Long.parseLong(p[1].trim());
                double actual = Double.parseDouble(p[2].trim());
                double predicted = Double.parseDouble(p[3].trim());
                double mem = p.length > 6 ? Double.parseDouble(p[5].trim()) : 0;
                int cores = p.length > 7 ? Integer.parseInt(p[6].trim()) : 1;
                byVm.computeIfAbsent(vmId, k -> new ArrayList<>())
                        .add(new TraceRow(vmId, ts, actual, predicted, mem, cores));
            }
        }
        byVm.values().forEach(list -> list.sort(Comparator.comparingLong(TraceRow::timestamp)));
        return byVm;
    }

    public static int commonStepCount(Map<Integer, List<TraceRow>> byVm, int maxSteps) {
        int minLen = byVm.values().stream().mapToInt(List::size).min().orElse(0);
        if (maxSteps > 0) {
            return Math.min(minLen, maxSteps);
        }
        return minLen;
    }
}

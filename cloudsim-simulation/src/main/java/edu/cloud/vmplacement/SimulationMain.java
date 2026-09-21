package edu.cloud.vmplacement;

import edu.cloud.vmplacement.config.SimulationConfig;
import edu.cloud.vmplacement.metrics.SimulationMetrics;
import edu.cloud.vmplacement.placement.AdaptiveRfPlacement;
import edu.cloud.vmplacement.placement.BestFitPlacement;
import edu.cloud.vmplacement.placement.FirstFitPlacement;
import edu.cloud.vmplacement.simulation.CloudSimBootstrap;
import edu.cloud.vmplacement.simulation.TraceDrivenSimulation;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.logging.Level;
import java.util.logging.Logger;

public final class SimulationMain {

    private static final Logger LOG = Logger.getLogger(SimulationMain.class.getName());

    public static void main(String[] args) throws Exception {
        Path configPath = Path.of(args.length > 0 ? args[0] : "../config/simulation_config.json");
        SimulationConfig config = SimulationConfig.load(configPath);
        applyLogLevel(config.logLevel);
        Path predictions = Path.of(config.predictionsCsv).normalize();
        if (!Files.isRegularFile(predictions)) {
            predictions = Path.of("..", "results", "predictions", "predictions.csv").normalize();
        }
        if (!Files.isRegularFile(predictions)) {
            throw new IllegalStateException("Predictions CSV not found. Run Python ML pipeline first: " + predictions);
        }

        CloudSimBootstrap.start();
        TraceDrivenSimulation engine = new TraceDrivenSimulation(config);
        Path resultsDir = Path.of(config.resultsDir);

        List<SimulationMetrics> all = new ArrayList<>();
        all.add(engine.run(new FirstFitPlacement(), predictions));
        all.add(engine.run(new BestFitPlacement(), predictions));
        all.add(engine.run(new AdaptiveRfPlacement(config, true), predictions));
        all.add(engine.run(new AdaptiveRfPlacement(config, false), predictions));

        Path comparisonCsv = resultsDir.resolve("comparison.csv");
        Files.createDirectories(resultsDir);
        StringBuilder sb = new StringBuilder(SimulationMetrics.csvHeader()).append('\n');
        for (SimulationMetrics m : all) {
            sb.append(m.toCsvRow()).append('\n');
            m.saveJson(resultsDir.resolve(m.method + ".json"));
        }
        Files.writeString(comparisonCsv, sb.toString());
        LOG.info("Wrote comparison results to " + comparisonCsv.toAbsolutePath());
    }

    static void applyLogLevel(String levelName) {
        Level level;
        try {
            level = Level.parse(levelName.trim().toUpperCase());
        } catch (IllegalArgumentException ex) {
            level = Level.WARNING;
        }
        Logger root = Logger.getLogger("");
        root.setLevel(level);
        for (var handler : root.getHandlers()) {
            handler.setLevel(level);
        }
        Logger.getLogger("edu.cloud.vmplacement").setLevel(level);
    }
}

import { useEffect, useMemo, useState } from "react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  BarChart,
  Bar,
} from "recharts";

const DEFAULTS = {
  method: "AdaptiveRF",
  host_count: 20,
  vm_count: 20,
  simulation_steps: 200,
  workload_intensity: 1,
  overload_threshold: 0.8,
  underload_threshold: 0.3,
  migration_cooldown_steps: 8,
  migration_margin: 0.05,
  carbon_intensity_kg_per_kwh: 0.5,
};

function fmt(n, d = 2) {
  if (n === undefined || n === null || Number.isNaN(n)) return "—";
  return Number(n).toFixed(d);
}

export default function App() {
  const [form, setForm] = useState(DEFAULTS);
  const [presets, setPresets] = useState({});
  const [ml, setMl] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [run, setRun] = useState(null);
  const [compareRows, setCompareRows] = useState(null);
  const [eventFilter, setEventFilter] = useState("all");

  useEffect(() => {
    fetch("/api/presets")
      .then((r) => r.json())
      .then((d) => setPresets(d.presets || {}))
      .catch(() => setError("Backend not reachable. Start FastAPI on port 8000."));
    fetch("/api/ml-metrics")
      .then((r) => (r.ok ? r.json() : null))
      .then(setMl)
      .catch(() => {});
  }, []);

  function setField(key, value) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  function applyPreset(name) {
    const p = presets[name];
    if (!p) return;
    setForm((f) => ({ ...f, ...p }));
  }

  async function runOne() {
    setBusy(true);
    setError("");
    try {
      const res = await fetch("/api/simulate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Simulation failed");
      setRun(data);
      setCompareRows(null);
    } catch (e) {
      setError(String(e.message || e));
    } finally {
      setBusy(false);
    }
  }

  async function runCompare() {
    setBusy(true);
    setError("");
    try {
      const res = await fetch("/api/compare", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Compare failed");
      setCompareRows(data.comparison);
      const chosen = data.details[form.method] || data.details.AdaptiveRF;
      setRun(chosen);
    } catch (e) {
      setError(String(e.message || e));
    } finally {
      setBusy(false);
    }
  }

  function resetAll() {
    setForm(DEFAULTS);
    setRun(null);
    setCompareRows(null);
    setError("");
  }

  async function downloadCsv() {
    const res = await fetch("/api/export/csv", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(form),
    });
    const text = await res.text();
    const blob = new Blob([text], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "simulation_comparison.csv";
    a.click();
    URL.revokeObjectURL(url);
  }

  function downloadSummary() {
    const payload = {
      config: form,
      summary: run?.summary,
      comparison: compareRows,
      ml,
    };
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "experiment_summary.json";
    a.click();
    URL.revokeObjectURL(url);
  }

  const s = run?.summary;
  const events = useMemo(() => {
    const list = run?.events || [];
    if (eventFilter === "all") return list.slice(-80);
    return list.filter((e) => e.type === eventFilter).slice(-80);
  }, [run, eventFilter]);

  return (
    <div className="page">
      <header>
        <h1>AI-Driven Adaptive VM Placement</h1>
        <p>Live numbers from the trace-driven simulator (Bitbrains RF predictions). Nothing is fabricated.</p>
      </header>

      <section className="panel">
        <h2>Scenario</h2>
        <div className="presets">
          {Object.keys(presets).length
            ? Object.keys(presets).map((name) => (
                <button key={name} type="button" onClick={() => applyPreset(name)}>
                  {name}
                </button>
              ))
            : ["Normal", "High Load", "Underutilized", "Overloaded", "Dynamic Workload"].map((name) => (
                <button key={name} type="button" disabled>
                  {name}
                </button>
              ))}
        </div>
        <div className="grid">
          <label>
            Algorithm
            <select value={form.method} onChange={(e) => setField("method", e.target.value)}>
              <option>FirstFit</option>
              <option>BestFit</option>
              <option>AdaptiveRF</option>
              <option>AdaptiveNoPrediction</option>
            </select>
          </label>
          <label>
            Hosts
            <input type="number" value={form.host_count} onChange={(e) => setField("host_count", +e.target.value)} />
          </label>
          <label>
            VMs
            <input type="number" value={form.vm_count} onChange={(e) => setField("vm_count", +e.target.value)} />
          </label>
          <label>
            Steps
            <input type="number" value={form.simulation_steps} onChange={(e) => setField("simulation_steps", +e.target.value)} />
          </label>
          <label>
            Workload intensity
            <input type="number" step="0.1" value={form.workload_intensity} onChange={(e) => setField("workload_intensity", +e.target.value)} />
          </label>
          <label>
            Overload threshold
            <input type="number" step="0.05" value={form.overload_threshold} onChange={(e) => setField("overload_threshold", +e.target.value)} />
          </label>
          <label>
            Underload threshold
            <input type="number" step="0.05" value={form.underload_threshold} onChange={(e) => setField("underload_threshold", +e.target.value)} />
          </label>
          <label>
            Migration cooldown (steps)
            <input type="number" value={form.migration_cooldown_steps} onChange={(e) => setField("migration_cooldown_steps", +e.target.value)} />
          </label>
          <label>
            Migration margin
            <input type="number" step="0.01" value={form.migration_margin} onChange={(e) => setField("migration_margin", +e.target.value)} />
          </label>
          <label>
            Carbon intensity (kg/kWh)
            <input type="number" step="0.05" value={form.carbon_intensity_kg_per_kwh} onChange={(e) => setField("carbon_intensity_kg_per_kwh", +e.target.value)} />
          </label>
        </div>
        <div className="actions">
          <button className="primary" type="button" disabled={busy} onClick={runOne}>
            {busy ? "Running…" : "Run Simulation"}
          </button>
          <button type="button" disabled={busy} onClick={runCompare}>
            Compare Algorithms
          </button>
          <button type="button" onClick={resetAll}>
            Reset
          </button>
          <button type="button" onClick={downloadCsv}>
            Download CSV
          </button>
          <button type="button" onClick={downloadSummary} disabled={!run}>
            Download summary
          </button>
        </div>
        {error ? <p className="error">{error}</p> : null}
      </section>

      {s ? (
        <section className="kpis">
          <Kpi label="Total energy" value={`${fmt(s.Energy_Wh)} Wh`} />
          <Kpi label="Average power" value={`${fmt(s.Avg_Power_W)} W`} />
          <Kpi label="Migrations" value={s.Migrations} />
          <Kpi label="SLA-risk intervals" value={s.SLA_Violations} />
          <Kpi label="Avg utilization" value={fmt(s.Avg_Utilization, 4)} />
          <Kpi label="Active hosts" value={`${s.Active_Hosts} / ${s.Active_Hosts + s.Inactive_Hosts}`} />
          <Kpi label="Carbon" value={`${fmt(s.Carbon_kg, 4)} kg`} />
          <Kpi label="Uses RF" value={s.uses_random_forest ? "yes" : "no"} />
        </section>
      ) : (
        <p className="hint">Run a simulation to fill KPI cards from real output.</p>
      )}

      {run?.timeseries?.length ? (
        <section className="charts">
          <Chart title="Energy over time (cumulative Wh)" data={run.timeseries} y="energy_wh_cumulative" />
          <Chart title="Average host CPU utilization" data={run.timeseries} y="avg_utilization" />
          <Dual title="Actual vs predicted mean VM CPU %" data={run.timeseries} />
          <Chart title="Migration events per step" data={run.timeseries} y="migrations" color="#d97706" />
          <Chart title="Active host count" data={run.timeseries} y="active_hosts" color="#2563eb" />
        </section>
      ) : null}

      {run?.layout?.length ? (
        <section className="panel">
          <h2>Data center (final layout)</h2>
          <div className="hosts">
            {run.layout.map((h) => (
              <article
                key={h.host_id}
                className={
                  "host-card" +
                  (!h.active ? " inactive" : "") +
                  (h.active && h.utilization > form.overload_threshold ? " overload" : "")
                }
              >
                <h3>Host {h.host_id}</h3>
                <p>{h.active ? "active" : "inactive"}</p>
                <p>util {(h.utilization * 100).toFixed(1)}%</p>
                <div className="bar">
                  <span style={{ width: `${Math.min(100, h.utilization * 100)}%` }} />
                </div>
                <div className="vms">
                  {(h.vm_ids || []).map((id) => (
                    <span key={id}>VM {id}</span>
                  ))}
                </div>
              </article>
            ))}
          </div>
        </section>
      ) : null}

      {run?.events ? (
        <section className="panel">
          <h2>Migration / consolidation events</h2>
          <div className="presets">
            {["all", "overload_migration", "consolidation", "host_inactive"].map((t) => (
              <button key={t} type="button" onClick={() => setEventFilter(t)}>
                {t}
              </button>
            ))}
          </div>
          <ol className="events">
            {events.map((e, i) => (
              <li key={`${e.step}-${e.type}-${i}`}>
                step {e.step}: {e.type}
                {e.vm_id !== undefined ? ` VM ${e.vm_id}` : ""}
                {e.from_host !== undefined ? ` ${e.from_host}→${e.to_host}` : ""}
                {e.host_id !== undefined ? ` host ${e.host_id}` : ""}
              </li>
            ))}
          </ol>
        </section>
      ) : null}

      {compareRows ? (
        <section className="panel">
          <h2>Comparison (same workload and config)</h2>
          <table>
            <thead>
              <tr>
                <th>Method</th>
                <th>Energy (Wh)</th>
                <th>Migrations</th>
                <th>SLA</th>
                <th>Avg util</th>
                <th>Active</th>
                <th>Inactive</th>
                <th>Carbon kg</th>
              </tr>
            </thead>
            <tbody>
              {compareRows.map((r) => (
                <tr key={r.Method}>
                  <td>{r.Method}</td>
                  <td>{fmt(r.Energy_Wh)}</td>
                  <td>{r.Migrations}</td>
                  <td>{r.SLA_Violations}</td>
                  <td>{fmt(r.Avg_Utilization, 4)}</td>
                  <td>{r.Active_Hosts}</td>
                  <td>{r.Inactive_Hosts}</td>
                  <td>{fmt(r.Carbon_kg, 4)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      ) : null}

      <section className="panel">
        <h2>Random Forest test metrics</h2>
        {ml ? (
          <>
            <p>
              RF MAE {fmt(ml.random_forest.mae, 4)} · RMSE {fmt(ml.random_forest.rmse, 4)} · R² {fmt(ml.random_forest.r2, 4)}
              {" "}(naive MAE {fmt(ml.naive_persistence.mae, 4)})
            </p>
            <p className="hint">These are chronological test-set scores from training, not a claim that RF placement is better.</p>
            {run?.timeseries?.length ? (
              <div className="chart-box">
                <ResponsiveContainer width="100%" height={240}>
                  <BarChart
                    data={[
                      { name: "MAE", Naive: ml.naive_persistence.mae, RF: ml.random_forest.mae },
                      { name: "RMSE", Naive: ml.naive_persistence.rmse, RF: ml.random_forest.rmse },
                    ]}
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="Naive" fill="#94a3b8" />
                    <Bar dataKey="RF" fill="#2563eb" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ) : null}
          </>
        ) : (
          <p className="hint">Train the model first: python src/run_ml_pipeline.py</p>
        )}
      </section>
    </div>
  );
}

function Kpi({ label, value }) {
  return (
    <div className="kpi">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function Chart({ title, data, y, color = "#059669" }) {
  return (
    <div className="chart-box">
      <h3>{title}</h3>
      <ResponsiveContainer width="100%" height={220}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="step" />
          <YAxis />
          <Tooltip />
          <Line type="monotone" dataKey={y} stroke={color} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

function Dual({ title, data }) {
  return (
    <div className="chart-box">
      <h3>{title}</h3>
      <ResponsiveContainer width="100%" height={220}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="step" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Line type="monotone" dataKey="mean_actual_cpu" name="Actual" stroke="#0f172a" dot={false} />
          <Line type="monotone" dataKey="mean_predicted_cpu" name="Predicted" stroke="#7c3aed" dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

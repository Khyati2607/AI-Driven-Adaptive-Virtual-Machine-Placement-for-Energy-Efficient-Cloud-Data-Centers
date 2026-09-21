"""
FastAPI dashboard backend. Runs the existing Python trace-driven simulator
(same algorithms as CloudSim Plus Java module) and returns real metrics.
"""

from __future__ import annotations

import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from simulate_datacenter import load_predictions, run_policy  # noqa: E402
from utils import load_json_config  # noqa: E402

METHODS = ["FirstFit", "BestFit", "AdaptiveRF", "AdaptiveNoPrediction"]

PRESETS: dict[str, dict[str, Any]] = {
    "Normal": {
        "host_count": 20,
        "vm_count": 20,
        "simulation_steps": 200,
        "workload_intensity": 1.0,
        "overload_threshold": 0.80,
        "underload_threshold": 0.30,
        "migration_cooldown_steps": 8,
        "migration_margin": 0.05,
        "carbon_intensity_kg_per_kwh": 0.5,
    },
    "High Load": {
        "host_count": 16,
        "vm_count": 24,
        "simulation_steps": 200,
        "workload_intensity": 2.5,
        "overload_threshold": 0.80,
        "underload_threshold": 0.25,
        "migration_cooldown_steps": 8,
        "migration_margin": 0.05,
        "carbon_intensity_kg_per_kwh": 0.5,
    },
    "Underutilized": {
        "host_count": 24,
        "vm_count": 12,
        "simulation_steps": 200,
        "workload_intensity": 0.5,
        "overload_threshold": 0.80,
        "underload_threshold": 0.30,
        "migration_cooldown_steps": 8,
        "migration_margin": 0.05,
        "carbon_intensity_kg_per_kwh": 0.5,
    },
    "Overloaded": {
        "host_count": 8,
        "vm_count": 24,
        "simulation_steps": 200,
        "workload_intensity": 3.0,
        "overload_threshold": 0.70,
        "underload_threshold": 0.25,
        "migration_cooldown_steps": 6,
        "migration_margin": 0.05,
        "carbon_intensity_kg_per_kwh": 0.5,
    },
    "Dynamic Workload": {
        "host_count": 20,
        "vm_count": 20,
        "simulation_steps": 300,
        "workload_intensity": 1.5,
        "overload_threshold": 0.80,
        "underload_threshold": 0.30,
        "migration_cooldown_steps": 10,
        "migration_margin": 0.05,
        "carbon_intensity_kg_per_kwh": 0.5,
    },
}

app = FastAPI(title="Adaptive VM Placement Dashboard API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SimRequest(BaseModel):
    method: str = "AdaptiveRF"
    host_count: int = Field(20, ge=1, le=80)
    vm_count: int = Field(20, ge=1, le=100)
    simulation_steps: int = Field(200, ge=10, le=800)
    workload_intensity: float = Field(1.0, ge=0.1, le=5.0)
    overload_threshold: float = Field(0.80, ge=0.4, le=1.0)
    underload_threshold: float = Field(0.30, ge=0.0, le=0.7)
    migration_cooldown_steps: int = Field(8, ge=0, le=50)
    migration_margin: float = Field(0.05, ge=0.0, le=0.3)
    carbon_intensity_kg_per_kwh: float = Field(0.5, ge=0.0, le=2.0)
    collect_timeseries: bool = True


def base_config() -> dict[str, Any]:
    return deepcopy(load_json_config("simulation_config.json"))


def merge_config(req: SimRequest) -> dict[str, Any]:
    cfg = base_config()
    cfg.update(
        {
            "host_count": req.host_count,
            "vm_count": req.vm_count,
            "simulation_steps": req.simulation_steps,
            "workload_intensity": req.workload_intensity,
            "overload_threshold": req.overload_threshold,
            "underload_threshold": req.underload_threshold,
            "migration_cooldown_steps": req.migration_cooldown_steps,
            "migration_margin": req.migration_margin,
            "carbon_intensity_kg_per_kwh": req.carbon_intensity_kg_per_kwh,
        }
    )
    return cfg


def predictions(vm_count: int) -> dict[int, list[dict[str, float]]]:
    path = ROOT / "results" / "predictions" / "predictions.csv"
    if not path.is_file():
        raise HTTPException(400, "Missing predictions.csv. Run: python src/run_ml_pipeline.py")
    data = load_predictions(path, vm_count)
    if not data:
        raise HTTPException(400, "No VM traces loaded from predictions.csv")
    return data


def slim_result(raw: dict[str, Any]) -> dict[str, Any]:
    ts = raw.get("timeseries") or []
    compact = [
        {
            "step": row["step"],
            "energy_wh_cumulative": row["energy_wh_cumulative"],
            "energy_wh": row["energy_wh"],
            "avg_utilization": row["avg_utilization"],
            "active_hosts": row["active_hosts"],
            "migrations": row["migrations"],
            "sla_violations": row["sla_violations"],
            "mean_actual_cpu": row["mean_actual_cpu"],
            "mean_predicted_cpu": row["mean_predicted_cpu"],
        }
        for row in ts
    ]
    return {
        "summary": {
            "Method": raw["Method"],
            "Energy_Wh": raw["Energy_Wh"],
            "Avg_Power_W": raw["Avg_Power_W"],
            "Peak_Power_W": raw["Peak_Power_W"],
            "Migrations": raw["Migrations"],
            "SLA_Violations": raw["SLA_Violations"],
            "Avg_Utilization": raw["Avg_Utilization"],
            "Active_Hosts": raw["Active_Hosts"],
            "Inactive_Hosts": raw["Inactive_Hosts"],
            "Carbon_kg": raw["Carbon_kg"],
            "Steps": raw["Steps"],
            "engine": raw.get("engine"),
            "uses_random_forest": raw.get("uses_random_forest"),
        },
        "timeseries": compact,
        "events": raw.get("events") or [],
        "layout": raw.get("layout") or [],
    }


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/presets")
def presets() -> dict[str, Any]:
    return {"presets": PRESETS, "methods": METHODS}


@app.get("/api/ml-metrics")
def ml_metrics() -> dict[str, Any]:
    path = ROOT / "results" / "ml" / "metrics.json"
    if not path.is_file():
        raise HTTPException(404, "Run python src/run_ml_pipeline.py first")
    return json.loads(path.read_text(encoding="utf-8"))


@app.post("/api/simulate")
def simulate(req: SimRequest) -> dict[str, Any]:
    if req.method not in METHODS:
        raise HTTPException(400, f"Unknown method {req.method}")
    cfg = merge_config(req)
    result = run_policy(req.method, cfg, predictions(req.vm_count), collect_timeseries=req.collect_timeseries)
    return slim_result(result)


@app.post("/api/compare")
def compare(req: SimRequest) -> dict[str, Any]:
    cfg = merge_config(req)
    by_vm = predictions(req.vm_count)
    rows = []
    details = {}
    for method in METHODS:
        raw = run_policy(method, cfg, by_vm, collect_timeseries=True)
        slim = slim_result(raw)
        rows.append(slim["summary"])
        details[method] = slim
    return {"comparison": rows, "details": details, "config": cfg}


@app.post("/api/export/csv")
def export_csv(req: SimRequest) -> PlainTextResponse:
    payload = compare(req)
    lines = [
        "Method,Energy_Wh,Avg_Power_W,Migrations,SLA_Violations,Avg_Utilization,Active_Hosts,Inactive_Hosts,Carbon_kg"
    ]
    for row in payload["comparison"]:
        lines.append(
            f"{row['Method']},{row['Energy_Wh']},{row['Avg_Power_W']},{row['Migrations']},"
            f"{row['SLA_Violations']},{row['Avg_Utilization']},{row['Active_Hosts']},"
            f"{row['Inactive_Hosts']},{row['Carbon_kg']}"
        )
    return PlainTextResponse("\n".join(lines) + "\n", media_type="text/csv")

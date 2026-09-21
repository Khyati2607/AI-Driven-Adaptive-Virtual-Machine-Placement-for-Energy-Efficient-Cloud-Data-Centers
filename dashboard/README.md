# Dashboard

React UI → FastAPI → existing Python simulator (same placement/energy logic as CloudSim Plus). Metrics are computed, not faked.

## 1. Train / predictions (once)

```powershell
cd "C:\Users\Ayush\Desktop\3 sub\AI-Driven-Adaptive-Virtual-Machine-Placement-for-Energy-Efficient-Cloud-Data-Centers"
pip install -r requirements.txt
python src/run_ml_pipeline.py
```

## 2. API

```powershell
python -m uvicorn dashboard.backend.app:app --app-dir . --host 127.0.0.1 --port 8000
```

If that import path fails:

```powershell
cd dashboard\backend
$env:PYTHONPATH = "..\..\src;..\.."
python -m uvicorn app:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000/api/health — should return `{"status":"ok"}`.

## 3. React UI

```powershell
cd dashboard\frontend
npm install
npm run dev
```

Open http://localhost:5173

Vite proxies `/api` to port 8000.

## Scenarios

Preset buttons: Normal, High Load, Underutilized, Overloaded, Dynamic Workload. Then **Run Simulation** or **Compare Algorithms**.

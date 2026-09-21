# ML Methodology

## Features (initial set)

- `CPU_lag_3`, `CPU_lag_2`, `CPU_lag_1`, `CPU usage [%]`
- Target: `CPU_target` = next-step CPU % (`shift(-1)`)

No future CPU in features. Lags computed **inside each VM** only.

## Model

`RandomForestRegressor(n_estimators=100, random_state=42)` — nonlinear, no scaling required, suitable for a student project vs heavier LSTM tuning.

## Baseline

Naive persistence: predict `CPU(t+1) = CPU(t)`.

## Split

First 80% of each VM timeline = train; last 20% = test. Random `train_test_split(shuffle=True)` would leak future information into lag rows.

## Why not LSTM (here)

LSTM can model long sequences but adds complexity, tuning cost, and harder viva explanation. RF + lags is a defensible baseline contribution when combined with adaptive placement.

# Viva / Interview Questions

1. **What is VM placement?** Mapping VMs to physical hosts subject to CPU/RAM constraints.
2. **Why important?** Affects utilization, energy, SLA risk, and migration cost.
3. **What is VM migration?** Moving a running VM from one host to another.
4. **Why costly?** Memory/state transfer, network bandwidth, downtime risk, extra CPU cycles.
5. **Consolidation?** Packing VMs onto fewer hosts to idle/power down empty machines.
6. **Why predict CPU?** Placement can look ahead and avoid reactive overload/underload oscillation.
7. **Why Random Forest?** Handles nonlinear patterns, robust to noise, no feature scaling, easier to explain than deep RNNs in a UG project.
8. **Why not linear regression?** Workloads are often nonlinear; linear model may underfit bursts.
9. **Why not LSTM?** Strong for sequences but heavier to train/tune/explain; RF+laws is a valid engineering tradeoff.
10. **Lag features?** Encode past CPU values at t-1,t-2,t-3 as inputs for predicting t+1.
11. **`shift(1)`?** Pulls previous row’s CPU into current row (lag).
12. **`shift(-1)`?** Pulls next row’s CPU as target (future label for supervised learning).
13. **Data leakage?** Using future information in training features so test scores look unrealistically good.
14. **No random shuffle?** Shuffling breaks time order and mixes future CPU into lag features for the same row window.
15. **MAE?** Average |actual − predicted|.
16. **RMSE?** sqrt(mean squared error); punishes large misses.
17. **R²?** 1 − SS_res/SS_tot; share of variance explained.
18. **CloudSim Plus?** Discrete-event cloud simulator (hosts, VMs, cloudlets, brokers).
19. **Host?** Physical machine with CPU, RAM, power model.
20. **VM?** Virtual machine with allocated resources on a host.
21. **Cloudlet?** Computational task/workload unit in CloudSim.
22. **SLA (here)?** Simulation rule: overload when host utilization exceeds configured threshold.
23. **QoS?** Only metrics the simulator actually computes (e.g., utilization, migration counts — not arbitrary web latency unless modeled).
24. **Energy?** Power × time; power increases with utilization in linear model.
25. **Carbon?** Energy × configurable grid carbon intensity — not a universal real-world constant.
26. **Migration overhead?** Modeled as fraction of VM CPU × time; real overhead varies by infrastructure.
27. **Novelty?** Combining trace-driven RF prediction with adaptive energy-aware placement and ablation vs FF/BF in one reproducible pipeline.
28. **Limitations?** Simulator, historical traces, lag-based RF, simplified power/migration/carbon assumptions.
29. **Why FF/BF baselines?** Standard, interpretable policies to show whether adaptive+ML adds value **only if experiments show it**.
30. **How prediction affects placement?** Adaptive policy uses predicted CPU to estimate future host load before migrate/consolidate decisions.

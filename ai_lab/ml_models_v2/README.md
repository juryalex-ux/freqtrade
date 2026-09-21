# Phase 3C conservative ML benchmark

This benchmark uses only the 1,271 unique Phase 3B Dataset A examples. Dataset B is
the same set of events and is deliberately never loaded or concatenated. The 2019–2024
period is development evidence: 2023 and 2024 were inspected in earlier phases and are
not pristine holdouts. No 2025, 2026, or sealed-shadow data is used.

Five expanding annual folds and exact row IDs come from
`ai_lab/ml_dataset_v2/folds.json`. Training labels must end before the evaluation-year
boundary minus a 48-hour embargo. Evaluation labels crossing the year's right boundary
are excluded. All pairs share calendar boundaries; rows are never shuffled.

Models and parameters are fixed in `protocol.json`. Preprocessing lives inside each
scikit-learn pipeline, so scalers and categorical encoders fit on that fold's training
rows only. The six feature sets include all features, a domain-reduced set, price/trend,
price/trend plus volatility, all excluding regime, and all excluding calendar fields.
The reduced-set removals are documented before model fitting and use no outcome values.

Economic results use out-of-fold probabilities at 0.50, 0.55, 0.60, 0.65, and 0.70.
They are reported per evaluation year and over all evaluation folds. Closed-subset
drawdown is calculated from selected trade P/L aggregated by close-day ordering; it is
not a Freqtrade wallet simulation. Empty selections remain visible. Results at these
thresholds are comparisons, not tuned strategy rules.

Feature importance uses the primary target and all features. Seven-day blocks are
permuted as blocks, with pair-specific diagnostics. Logistic coefficients are retained
for every feature set and fold. Rank stability is descriptive because examples and
labels overlap in time; no IID confidence interval is claimed.

Run from the repository root:

```powershell
.venv/Scripts/python.exe -B ai_lab/ml_models_v2/test_protocol.py
.venv/Scripts/python.exe -B ai_lab/ml_models_v2/benchmark.py
.venv/Scripts/python.exe -B ai_lab/ml_models_v2/test_protocol.py
.venv/Scripts/python.exe -B ai_lab/ml_models_v2/report.py
```

No prediction is integrated into Freqtrade, and no strategy or core file is changed.

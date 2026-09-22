# Phase 5B — deterministic alpha failure diagnosis

This workspace diagnoses the five existing strategies using only their previously used 2019–2022 development trades and candles. It does not run strategy entry logic, change parameters, construct filters, or create a candidate.

The diagnostic protocol freezes alignment, horizon, excursion, first-passage, recovery, continuation, regime, volatility, session, duration, fee, and trimming definitions before analysis. Future price data appears only in explicitly named diagnostic outcomes.

Run from the repository root:

```powershell
.venv\Scripts\python.exe -B ai_lab\alpha_diagnostics\freeze.py
.venv\Scripts\python.exe -B ai_lab\alpha_diagnostics\analyze.py
.venv\Scripts\python.exe -B ai_lab\alpha_diagnostics\report.py
.venv\Scripts\python.exe -B ai_lab\alpha_diagnostics\test_audit.py
.venv\Scripts\python.exe -B ai_lab\alpha_diagnostics\finalize.py
```

The evidence is diagnostic and retrospective. It is not a holdout evaluation and does not authorize paper or live trading.

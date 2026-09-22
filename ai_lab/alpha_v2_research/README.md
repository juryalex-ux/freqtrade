# Phase 5A — deterministic alpha architecture research

This isolated workspace evaluates exactly three frozen causal architectures on BTC/USDT and ETH/USDT, 1h, using December 2018 only for warmup and calendar years 2019–2022 for scoring. It never loads or evaluates 2023+ data.

The sequence is locked: reuse the already-audited 2018–2022 data and frozen references, run `freeze.py`, run causality tests, run `run.py` once, then generate the report and final integrity inventory. The manifest records all definitions, parameters, hashes, fee assumptions, execution behavior, and continuation criteria before results exist.

Commands from the repository root:

```powershell
.venv\Scripts\python.exe -B ai_lab\alpha_v2_research\freeze.py
.venv\Scripts\python.exe -B ai_lab\alpha_v2_research\test_causality.py
.venv\Scripts\python.exe -B ai_lab\alpha_v2_research\run.py
.venv\Scripts\python.exe -B ai_lab\alpha_v2_research\report.py
.venv\Scripts\python.exe -B ai_lab\alpha_v2_research\finalize.py
```

All results are development research. No candidate is integrated, paper traded, or enabled for live trading.

# Phase 4B locked retrospective robustness

AlphaBreakout is frozen exactly from the Phase 4A central candidate. The manifest
captures source/config hashes, parameter values, fees, pairs, timeframe, execution,
Git commit and freeze time before later-period data or outcomes are used.

The four evaluated periods are historical project evidence only:

| Label | Interval |
| --- | --- |
| A_2023 | 2023-01-01 through 2024-01-01 exclusive |
| B_2024 | 2024-01-01 through 2025-01-01 exclusive |
| C_2025_to_2026Q1 | 2025-01-01 through 2026-04-01 exclusive |
| D_2026_shadow | 2026-04-01 through 2026-09-01 exclusive |

They have all been observed in earlier project phases. No result is an untouched
holdout and no result can change AlphaBreakout. D uses the existing sealed price
files byte-for-byte and is treated as consumed historical evidence.

The independent source copy includes the complete Phase 4A candidate file but the
runner invokes only AlphaBreakout and the permanent LabBaseline reference. The
original LabBaseline file is never altered. No ML, FreqAI, neural network, real
trading, parameter change, indicator addition or favorable-period selection occurs.

Before period A, Dec 2022 supplies warmup. A-C come from end-bounded public Binance
requests through 2026-04-01. D appends the exact sealed data. One confirmed 2023
gap per pair follows the documented lab policy: synthetic prior-close OHLC and zero
volume, retained as an audit flag. The engine receives 1h OHLCV and all backtests
use Freqtrade next-candle execution with 0.1% fee per side.

Run only once from the repository root; completed evidence is never overwritten:

```powershell
.venv/Scripts/python.exe -B ai_lab/alpha_validation/freeze.py
.venv/Scripts/python.exe -B ai_lab/alpha_validation/download.py
.venv/Scripts/python.exe -B ai_lab/alpha_validation/test_causality.py
.venv/Scripts/python.exe -B ai_lab/alpha_validation/run.py
.venv/Scripts/python.exe -B ai_lab/alpha_validation/report.py
.venv/Scripts/python.exe -B ai_lab/alpha_validation/finalize.py
```

See reports/comparison.md for results and reports/file-inventory.txt for every
artifact. The category only states whether the frozen alpha may be considered for
a future prospective protocol. It never claims live profitability.

# Freqtrade AI Lab — Phase 1

Isolated comparison workspace on `ai-lab-development`. Freqtrade core is unchanged.
Phase 1 contains a deterministic baseline, not a trained AI model. Live trading is
disabled in both configurations. Only Binance spot BTC/USDT and ETH/USDT are used.

## Prerequisites

Phase 1.5 validated this checkout with its existing isolated `.venv` (Python
3.12.0, 64-bit). Run `.venv/Scripts/python.exe` explicitly; the system Python
is not the project environment. Official `requirements.txt` is installed, and
`pip check` passes. The checkout is installed editable from `pyproject.toml`.
See `reports/baseline-2025-Q1.md` for results and limitations and
`reports/commands-phase1.5.md` for setup and execution details.
Binance public market-data access must be available from your location.
No exchange account or API credentials are needed for these operations.

## First data download and backtest (PowerShell)

```powershell
Set-Location C:\Users\ip1ip\Documents\freqtrade
git branch --show-current
git status
.venv/Scripts/python.exe -m freqtrade --version
.venv/Scripts/python.exe ai_lab/run.py download
.venv/Scripts/python.exe ai_lab/run.py backtest
```

Stop if the branch is not `ai-lab-development` or any command fails. The runner
also checks the branch, rejects all `FREQTRADE__` environment overrides, requires
paper trading and the two-pair whitelist, and rejects credentials and additional
config files. It accepts no extra Freqtrade arguments. Do not bypass it for lab runs.
The `.env.example` file documents future variable names only; it is not loaded.

Download fetches 1-hour candles from 2024-12-01 through 2025-04-01 (exclusive),
including warmup data. Backtesting compares 2025-01-01 through 2025-04-01
(exclusive), disables cached results, exports trades to `ai_lab/results`, and
assumes a fee of 0.1% on each side. This is a comparison assumption, not a claim
about your account's fees. Check downloaded candle coverage before interpreting results.

The baseline enters long when SMA(20) crosses above SMA(50), and exits on the
reverse crossover, a 5% ROI target, or a 5% stop loss. It uses 51 warmup candles,
positive-volume signals, no leverage, no shorts, no trailing stop, and no optimization.
Starting simulated capital is 1,000 USDT, stake is 100 USDT, and at most two trades
may be open. Stop losses do not guarantee execution at the requested price.

## Dry-run

```powershell
Set-Location C:\Users\ip1ip\Documents\freqtrade
.venv/Scripts/python.exe ai_lab/run.py dry-run
```

This uses current public market data and simulated orders. Stop with Ctrl+C.
The runner additionally passes `--dry-run` explicitly. The persistent simulated
trade database is `ai_lab/results/dry-run.sqlite`; subsequent runs reuse it.
Logs are written to `ai_lab/logs`. Telegram and the API server are disabled.
The historical backtest fee is fixed by the runner; dry-run can use exchange fee
metadata, so record differences when comparing results.

## Workspace

| Path | Purpose |
| --- | --- |
| `configs/backtest.json` | Standalone reproducible backtest settings |
| `configs/dry-run.json` | Paper-trading settings and isolated SQLite database |
| `strategies/LabBaseline.py` | Frozen starting benchmark for later experiments |
| `run.py` | Restricted download, backtest and paper-trading entry point |
| `data/` | Downloaded public candles |
| `experiments/` | Future experiment specifications; keep baseline unchanged |
| `logs/` | Runtime diagnostics |
| `reports/` | Human-reviewed comparison and validation reports |
| `results/` | Backtest exports and paper-trading database |
| `.env.example` | Commented credential-variable placeholders |
| `.gitignore` | Excludes secrets and generated data, logs, reports and results |
| `VALIDATION_CHECKLIST.md` | Required review gates before any future live phase |

Each empty workspace folder has a `.gitkeep` to retain its structure in Git.
For each future experiment, record the Git revision, strategy and configuration,
data coverage, timerange, fees, trade count, drawdown and performance relative to
this baseline. Review results before deliberately versioning any generated report.
Phase 1 ends with review: no live config, push, merge, or core changes are included.

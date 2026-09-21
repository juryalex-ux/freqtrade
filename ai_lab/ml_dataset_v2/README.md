# Phase 3B: expanded observed-history datasets

**All 2019–2024 data is development history. 2023 and 2024 were already inspected.**
2024 is an internal evaluation slice, not a pristine or untouched validation set.
No 2025/2026 prices, consumed-test data or sealed shadow data are read. No ML,
hyperparameter optimization or strategy changes occur.

## Historical data

Binance spot BTC/USDT and ETH/USDT, hourly, Jan 1 2019 through Dec 31 2024.
Dec 2018 is past-only indicator warmup; no 2018 examples are included. Requests
explicitly set endTime to 2024-12-31 23:59:59.999 UTC, so pagination cannot silently
fetch 2025 prices. Full common history is available for both pairs, with documented
short gaps. Raw Feather files preserve the exchange observations without deduping,
sorting or hiding anomalies. Audit failures stop the build.

Sixty absent hourly timestamps per pair were individually re-requested and confirmed
absent. Every gap is at most 12 hours; longer outages require review and stop the
download script. Working candles explicitly mark `synthetic=True` and use the
last available close for OHLC and zero volume. This is a disclosed interpolation
policy, not fabricated observed history. Raw counts and filled counts are reported
separately. Indicators and trades can be influenced by filled bars; these years
must not be described as pristine. Existing zero-volume bars are retained too.

Price audits assert nonnegative volume, positive prices and coherent OHLC bounds.
Close-to-close changes >10% and open/prior-close gaps >2% are flagged for review,
not deleted or winsorized. Flags can be real market events, not necessarily bad data.

## Frozen strategy and the two datasets

LabBaseline's SHA-256 must match the existing frozen hash. SMA20/50, ROI 5%,
stoploss -5%, volume gate, order types and exits are unchanged. Both runs use the
same Freqtrade engine, 0.1% fee each side and 100-USDT stake. Current exchange
metadata is used; historical precision/minimum-order rules are not reconstructed.

Dataset A is a continuous 2019–2024 portfolio backtest, initial wallet 1,000 USDT,
at most two trades and one position per pair. It is not six reset yearly portfolios.
Year attribution uses entry year; a trade may exit in the next year. Thus year
figures need not reproduce older single-year backtests with forced boundary exits.

Dataset B uses Freqtrade's backtest-only position stacking, unlimited trade slots
and a sufficiently large simulated wallet to remove capital suppression. This
changes portfolio constraints only, never entry/exit logic or stake. Every valid
upward crossover is independently reconciled to exactly one trade, with no extra,
missing or duplicate entry. Shared trades must match A's ratio, exit, duration,
MFE and MAE. Aggregate B wallet returns are meaningless and are not promoted as
portfolio performance. The engine ZIP includes its diagnostic wallet results,
but the dataset/report uses per-signal net profits.

For this particular baseline A and B contain the same entries. A new upward SMA
cross follows a downward cross that generally closes the prior position, and the
two-pair/two-slot portfolio rejected no signals. B therefore adds no new examples.
Never concatenate A and B as independent observations: they duplicate the same
economic events. Historical expansion, not independent simulation, increases size.

## Features and labels

Phase 2C features are imported without modifying the originals. Three redundancies
are removed: body_ratio, raw atr14, and macd_hist_ratio. Seven retained additions
cover weekly momentum, relative volatility/ATR, directional persistence,
volume-price interaction, range expansion and signal density. Exact
formulas are in schema.json and feature_builder.py. Total: 42 numeric predictors
plus categorical pair and regime. No feature selection is performed using labels.

Features for entry t come from the candle stamped t−1h, available when t begins.
All rolling statistics use current/past observations, no centered windows or
future fill. Before enough past data exists, warmup values remain missing; the
completed datasets must have finite, complete feature rows. Phase 2B labels use
the unchanged causal detector. No future-return class becomes a predictor.

Frozen outcomes: exported net profit ratio and USDT already include fees; binary
targets use strict >0, >0.005 and >0.01 thresholds. stoploss_hit uses the original
stop_loss exit. Duration is in minutes. Gross MFE=max(0,max_rate/open_rate−1),
MAE=min(0,min_rate/open_rate−1), using engine-observed hourly excursions. These are
not tick-exact intrabar paths. Exit reason and boundary force-exit flag are labels/
metadata only. End-of-data positions are force-closed and flagged.

Diagnostic forward returns at 6/12/24/48h use close[i+h]/close[i]−1, where i is
the feature candle at t−1h. They are gross, not fee-adjusted, and are LABELS ONLY.
Their observation ends at t+h. Missing tail horizons remain null and flagged;
no 2025 data is downloaded to complete them. label_end is conservatively the
later of strategy exit and entry+48h, even for censored final examples. A metadata
deadline can extend past Dec 2024 without reading any price at that deadline.

## Chronological nested development and overlap

- Historical training pool: 2019–2022.
- Internal development: 2023 (previously observed).
- Internal evaluation: 2024 (previously observed, not a pristine holdout).
- Expanding audit folds: train from 2019, evaluate each full year 2020–2024.

folds.json stores exact train/test row IDs for both datasets. A training row is
eligible only if both entry and label_end precede the next test year's start
minus a 48-hour embargo. Evaluation rows whose label_end reaches/passes that
year's exclusive end are excluded. This protects both strategy outcomes and the
longest diagnostic horizon. Both pairs use shared calendar boundaries; never
random-shuffle or independently split overlapping outcomes. Within-fold labels
remain dependent; overlap counts and maximum concurrency are recorded. Any later
uncertainty estimate must use time-aware blocks, not IID trade bootstrap.

## Audits and reproduction

From the repository root with the existing project venv:

```powershell
.venv/Scripts/python.exe -B ai_lab/ml_dataset_v2/download.py
.venv/Scripts/python.exe -B ai_lab/ml_dataset_v2/run_baselines.py
.venv/Scripts/python.exe -B ai_lab/ml_dataset_v2/build.py
.venv/Scripts/python.exe -B ai_lab/ml_dataset_v2/test_quality.py
.venv/Scripts/python.exe -B ai_lab/ml_dataset_v2/audit.py
.venv/Scripts/python.exe -B ai_lab/ml_dataset_v2/report.py
```

The backtest wrapper refuses to overwrite finished ZIP evidence. No extra packages
are required. Do not run with -O: assertions enforce invariants. The statistical
audits report Pearson/Spearman correlations, redundancy at |r|>=0.98, suspicious
feature/outcome correlations at |r|>=0.95, pair/year distributions and drift. Drift
uses pair-specific 2019 reference means/std and KS statistics; no model is fitted.
Raw pair KS statistics and year drift are descriptive, not independent-sample
significance tests. Small regime cells and many comparisons limit interpretation.

Each dataset has Parquet plus separate feature/outcome CSVs. Do not feed all
Parquet columns to a model; use the schema's feature whitelist. reports/summary.md
contains the review, and reports/file-inventory.txt lists every created file.

The initially proposed rolling_drawdown_168 was removed after a feature-only
redundancy check found |r|>0.98 with existing distance_high_168 in every year.
The pre-consolidation audit is preserved. No outcome-based feature selection
was used. Final count is 44 predictors (42 numeric and two categorical).

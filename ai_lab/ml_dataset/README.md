# Phase 2C: causal actual-trade learning dataset

No model is trained. No features, thresholds or strategy parameters are optimized.
The population is actual LabBaseline trades only (allowed by the requested
opportunities and/or actual-trades scope), not every crossover or rejected order.
This introduces baseline-selection conditioning and must not be mistaken for a
general market-opportunity sample.

## Scope and files

- Development: entries and exits within 2023-01-01 through 2024-01-01 exclusive.
- Validation: entries and exits within 2024-01-01 through 2025-01-01 exclusive.
- Pairs: BTC/USDT and ETH/USDT, hourly spot data. UTC throughout.
- Dec 2022 candles are past-only indicator warmup; no warmup rows are examples.
- No consumed final-test or sealed-shadow paths are read; no 2025+ data is used.
- Existing baseline trade outcomes are reused without rerunning or modifying it.

Each split has a feature CSV, outcome CSV and a joined Parquet dataset. Join using
`row_id`; rows are sorted by decision_time then pair, never randomly shuffled.
`schema.json` lists the only permitted future-model feature columns and exact
formulas/windows. The joined dataset also contains outcomes and metadata: never
feed all its columns into a model. `outcome_end`, `row_id`, `split`, timestamps,
excursions, exit reasons and target columns are not numeric predictor inputs.
Pair is a categorical feature and identifier; regime is categorical. Total:
40 features (38 numeric plus pair and regime).

## Decision-time alignment

A trade entering at time t receives features from the complete hourly candle
opening at t−1h, available at t. Entry fill price, duration, exit, profit and future
high/low never enter the feature builder. Hour/day describe the known decision
timestamp. Indicators continue chronologically across the year boundary, using
past information only. All windows are trailing and include the decision candle.
EMAs use adjust=False; rolling standard deviations use ddof=1. Rolling volatility
percentiles use only the trailing 720 observations, never a full-sample rank.

`candles_since_prior_signal` counts from the last baseline SMA20/50 upward cross
strictly before the decision candle. Excluding the current cross avoids making
this feature identically zero on crossover entries. The historical cross also
requires positive volume, matching the baseline. Before any prior signal it is
missing, not future-filled. No completed dataset row requires this imputation.

The Phase 2B regime implementation is imported unchanged. Regime duration counts
consecutive candles with the same label, including the current one; transition
compares only with the preceding label. No labels from future price returns are
used as features. Historical source gaps are filled only using previous close,
never subsequent prices. The known 2023-03-24 13:00 UTC gap is flagged synthetic.
Source files and trade-result files are hashed in audits/source-manifest.json.

## Outcome definitions

| Outcome | Definition |
| --- | --- |
| net_profit_ratio | Freqtrade exported profit_ratio, already after entry/exit fees |
| win_loss | win if net ratio > 0; loss if < 0; otherwise flat |
| profitable_after_fees | net ratio > 0 |
| return_above_0_5_percent | net ratio strictly > 0.005 |
| return_above_1_percent | net ratio strictly > 0.01 |
| mfe_ratio | max(0, exported max_rate / entry open_rate − 1) |
| mae_ratio | min(0, exported min_rate / entry open_rate − 1), negative adverse excursion |
| duration_minutes | Exported trade duration |
| exit_reason | Original exported exit reason, including boundary force exits |
| stoploss_hit | Exported exit reason is stop_loss, trailing_stop_loss or stoploss_on_exchange |
| favorable_move_before_adverse_move | First gross +1% high barrier precedes first gross −1% low barrier during [entry, exit); see below |

Excursions are gross-price, engine-observed, hourly-resolution estimates. They are
not after-fee trade returns or tick-accurate intrabar extrema. First-passage labels
use observed high/low barriers relative to the fill price; a sole favorable hit
is 1 and a sole adverse hit is 0. If the earliest favorable/adverse hits occur
in the same hour, label is null (`same_hour_ambiguous`). If neither is observed,
label is null (`neither_barrier_observed`). The exit candle is excluded because
its full range can extend after the exit fill. Entry-hour range can also have
intrabar fill-order uncertainty: these are coarse candle-based labels, not a
claim to know tick ordering. No unknown outcomes are imputed as losses.

## Checks and audit

Synthetic tests verify prefix equality, future-price/volume mutation invariance,
decision-time alignment, warmup NaNs remaining unfilled, flat/zero-volume behavior,
ambiguous barriers and exclusion of post-exit candle values. Real-data tests
compare prefix-recomputed values and perturb future observations. Builder checks
duplicate row IDs and pair/timestamp keys, chronological ordering, finite complete
features, disjoint splits and outcome intervals, feature/outcome column separation,
and the frozen LabBaseline hash.

Reports contain per-split/per-pair numeric distributions (including tail quantiles),
label balances, all numeric Pearson/Spearman feature/outcome correlations, pair
differences and regime-conditioned outcomes. Absolute feature/outcome correlation
>=0.95 is flagged for investigation; feature/feature Pearson >=0.98 is reported
as redundancy, not automatically leakage. No feature is selected or removed using
these audits. Constant features have undefined correlation and are skipped, not
reported as zero. Categorical pair/regime comparisons use grouped summaries.

Correlation screening across many correlated indicators risks false discoveries.
This small, trade-selected dataset cannot establish an edge. Validation is viewed
for descriptive auditing here; future selection based on it must acknowledge that
use and reserve a separately authorized untouched holdout for final evaluation.
The sealed shadow remains untouched.

## Reproduce from the repository root

```powershell
.venv/Scripts/python.exe -B ai_lab/ml_dataset/test_features.py
.venv/Scripts/python.exe -B ai_lab/ml_dataset/build.py
.venv/Scripts/python.exe -B ai_lab/ml_dataset/audit.py
```

Do not run with Python -O: assertions enforce integrity checks. No network or
package installation is required. File inventory is in reports/file-inventory.txt.

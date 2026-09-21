# Phase 3D single-shot shadow evaluation

**C. No evidence of reliable ML edge for this frozen candidate.**

The candidate selected two trades, both ETH losses. Net P/L was -3.5900 USDT versus +1.3002 USDT unfiltered.
Overall ranking was near random, and pair ranking contradicted sharply. This does not justify paper-trading integration.
It is not a claim that every possible ML approach is ineffective. This period is now consumed and must never guide retuning.

## Frozen candidate

- LogisticRegression, Phase 3C B_reduced, 36 raw predictors (34 numeric + pair/regime).
- L2: C=0.1, l1_ratio=0, lbfgs, max_iter=2000, tol=0.0001, no class weights, seed 31415.
- StandardScaler and dense OneHotEncoder(handle_unknown="ignore"), fitted on development only.
- Target profitable_after_fees; threshold 0.55. No calibration refit or alternative thresholds.
- 1,271 training trades: 2019-01-01 through 2024-12-31. All labels used for fitting end in 2024.
- Shadow 2026-04-01 inclusive through 2026-09-01 exclusive. March 2026 is feature warmup only.
- Fee 0.1% each side; fixed 100 USDT stake; 1,000 USDT wallet; two open trades maximum.
- Freeze UTC: 2026-09-21T18:56:40.324081+00:00; Git commit: ab97681ec1089a0acd834a3b5dc046beda8f019a.
- Manifest SHA256: 31f2af6390965cfeb1066e168c78c009301d7b4a32a2773abc04dfc88c9c9722
- Fitted model SHA256: 6db15e010e84fb6f7047b41adb8b35f9571e2b7c227a072b6724460967b84f64

Exact feature list:

ema20_distance, ema50_distance, ema20_slope_6, ema50_slope_6, trend_efficiency_20, range_ratio, body_to_range, close_location, natr14, return_std_24, return_std_168, volatility_percentile_720, rsi14, macd_ratio, relative_volume_24, volume_zscore_24, volume_trend_24_168, regime_duration, regime_transition, hour_of_day, day_of_week, distance_high_168, distance_low_168, candles_since_prior_signal, pair, regime, return_1h, return_6h, return_24h, return_168h, volatility_ratio_24_168, natr_ratio_168, up_fraction_24, volume_price_interaction, range_expansion_24, signal_density_168

## Classification at frozen threshold 0.55

| Metric | All | BTC | ETH |
| --- | ---: | ---: | ---: |
| n | 78.0000 | 36.0000 | 42.0000 |
| prevalence | 0.3846 | 0.4167 | 0.3571 |
| roc_auc | 0.5271 | 0.6825 | 0.3728 |
| pr_auc_ap | 0.3960 | 0.6113 | 0.3000 |
| balanced_accuracy | 0.4792 | 0.5000 | 0.4630 |
| precision | 0.0000 | 0.0000 | 0.0000 |
| recall | 0.0000 | 0.0000 | 0.0000 |
| f1 | 0.0000 | 0.0000 | 0.0000 |
| brier | 0.2473 | 0.2316 | 0.2608 |
| ece_5_bins | 0.1119 | 0.1035 | 0.1942 |
| mean_probability | 0.3330 | 0.3237 | 0.3410 |

Confusion matrices are [[TN, FP], [FN, TP]]:
- ALL: [[46, 2], [30, 0]]
- BTC/USDT: [[21, 0], [15, 0]]
- ETH/USDT: [[25, 2], [15, 0]]

The uninformative-ranking AP reference is target prevalence: 0.3846 overall. Observed AP 0.3960 is only 0.0114 higher.
The standard Phase 3C classification cutoff 0.50 is separately retained in classification.json for compatibility, not as another economic rule.

## Economics after fees

| Metric | Unfiltered LabBaseline | Frozen filter |
| --- | ---: | ---: |
| trades | 78.0000 | 2.0000 |
| retention_pct | 100.0000 | 2.5641 |
| wins | 30.0000 | 0.0000 |
| losses | 48.0000 | 2.0000 |
| win_rate_pct | 38.4615 | 0.0000 |
| net_usdt | 1.3002 | -3.5900 |
| return_on_1000_pct | 0.1300 | -0.3590 |
| average_trade_pct | 0.0169 | -1.7970 |
| profit_factor | 1.0169 | 0.0000 |
| expectancy_usdt | 0.0167 | -1.7950 |
| closed_trade_max_drawdown_pct | 1.7107 | 0.3590 |
| consecutive_losses | 7.0000 | 2.0000 |
| average_duration_minutes | 2610.0000 | 2610.0000 |

Net change versus unfiltered: -4.8902 USDT.
Unfiltered start/end balance: 1000 / 1001.3002 USDT. Filtered realized subset ending equity: 996.4100 USDT.
Full Freqtrade unfiltered wallet-statistics drawdown is 2.3369%, distinct from closed-trade drawdown.
Filtered drawdown is closed-trade subset equity; no filtered intratrade wallet simulation was run.

## Pair economics

| Pair | Baseline trades | Baseline net | Selected | Retention | Filter net | Filter PF |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| BTC/USDT | 36 | -0.0931 | 0 | 0.00% | 0.0000 | N/A |
| ETH/USDT | 42 | 1.3933 | 2 | 4.76% | -3.5900 | 0.0000 |

Regime counts at entry:

- Unfiltered: {'RANGE': 55, 'TREND_UP': 15, 'LOW_VOLATILITY': 7, 'TREND_DOWN': 1}
- Filtered: {'TREND_UP': 2}

## Audits and technical recovery

- Manifest, fitted model, preprocessing and all frozen source hashes were recorded before unsealing; all still match.
- Model/scaler/encoder fitted once on 2019-2024 development rows before shadow access. No 2025/2026 data in fitting.
- Exactly one baseline backtest and one predict_proba call; no setting changes or alternate evaluations.
- Original seal and both price files still match their original SHA256 values.
- Each pair: 3,672 shadow hours and 744 March warmup hours, no missing or duplicate candles.
- Each pair: 12 real prefix checks, future mutation and no future-fill checks passed.
- 78 unique trades; no NaN/infinite predictors; all feature candles completed before entry.
- Three synthetic/protocol tests passed. One boundary force exit; no rejected baseline entry signals.
- Two technical stops occurred before any predictions or backtests: dtype-sensitive timestamp equality, then mixed datetime concatenation. Audited recovery normalized representation while asserting unchanged timestamps. Frozen files and model parameters were preserved.
- Freqtrade warns that data ends at Aug 31 23:00; this is the required last hourly candle before the end-exclusive Sep 1 boundary.
- Predeclared drawdown correction uses close times. Raw economics.json also misnamed the engine closed-trade statistic as wallet drawdown; economic-comparison.json corrects that name/value from existing wallet_stats only.
- Consumption is recorded in CONSUMED.json here; original SEALED.json remains historical evidence. Do not regard it as an unused seal.
- All observed integrity/leakage checks pass; tests cannot prove absence of every possible defect. Small samples and common market exposure limit inference.

## Scope

No core/strategy or existing tracked files changed. Phase 3C untracked files were preserved. No integration, commit, push or merge.
All new deliverables are listed in file-inventory.txt and hashed in artifact-sha256.json.

## Git status

```text
?? ai_lab/ml_models_v2/
?? ai_lab/ml_shadow/
```

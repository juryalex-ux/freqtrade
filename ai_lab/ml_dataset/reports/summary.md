# Phase 2C dataset audit

Actual baseline trades only; no model trained and no features selected from correlations.

| Split | Target | Positive | Negative | Unknown | Positive % of known |
| --- | --- | ---: | ---: | ---: | ---: |
| development | profitable_after_fees | 72 | 145 | 0 | 33.18 |
| development | return_above_0_5_percent | 57 | 160 | 0 | 26.27 |
| development | return_above_1_percent | 46 | 171 | 0 | 21.20 |
| development | stoploss_hit | 8 | 209 | 0 | 3.69 |
| development | favorable_move_before_adverse_move | 87 | 92 | 38 | 48.60 |
| validation | profitable_after_fees | 73 | 132 | 0 | 35.61 |
| validation | return_above_0_5_percent | 59 | 146 | 0 | 28.78 |
| validation | return_above_1_percent | 50 | 155 | 0 | 24.39 |
| validation | stoploss_hit | 15 | 190 | 0 | 7.32 |
| validation | favorable_move_before_adverse_move | 98 | 91 | 16 | 51.85 |

## Largest simple correlations with net profit ratio

Within each split independently; Pearson correlations, exploratory only.

| Split | Feature | Pearson r | n |
| --- | --- | ---: | ---: |
| development | return_12h | -0.2178 | 217 |
| development | ema50_distance | -0.2044 | 217 |
| development | distance_high_168 | -0.1966 | 217 |
| development | distance_low_24 | -0.1884 | 217 |
| development | ema20_distance | -0.1859 | 217 |
| validation | regime_transition | 0.1604 | 205 |
| validation | distance_high_168 | 0.1587 | 205 |
| validation | candles_since_prior_signal | -0.1366 | 205 |
| validation | return_3h | 0.1359 | 205 |
| validation | return_std_168 | -0.1221 | 205 |

Feature/outcome correlations with |r| >= 0.95: 0.
Feature/feature pairs with |Pearson r| >= 0.98: 2; inspect correlation-flags.json.
No flag is proof of absence of leakage; temporal construction and perturbation tests are separate checks.

## Pair differences

| Split | Pair | Rows | Win % | Mean net return % |
| --- | --- | ---: | ---: | ---: |
| development | ALL | 217 | 33.18 | -0.028 |
| development | BTC/USDT | 115 | 32.17 | -0.154 |
| development | ETH/USDT | 102 | 34.31 | 0.115 |
| validation | ALL | 205 | 35.61 | -0.212 |
| validation | BTC/USDT | 106 | 41.51 | -0.022 |
| validation | ETH/USDT | 99 | 29.29 | -0.416 |

## Regime-conditioned outcomes

| Split | Pair | Regime | Rows | Win % | Mean net return % |
| --- | --- | --- | ---: | ---: | ---: |
| development | BTC/USDT | LOW_VOLATILITY | 22 | 18.18 | -0.087 |
| development | BTC/USDT | RANGE | 68 | 36.76 | 0.119 |
| development | BTC/USDT | TREND_DOWN | 2 | 50.00 | -1.238 |
| development | BTC/USDT | TREND_UP | 23 | 30.43 | -0.932 |
| development | ETH/USDT | LOW_VOLATILITY | 11 | 9.09 | -0.313 |
| development | ETH/USDT | RANGE | 69 | 39.13 | 0.400 |
| development | ETH/USDT | TREND_DOWN | 1 | 100.00 | 0.922 |
| development | ETH/USDT | TREND_UP | 21 | 28.57 | -0.635 |
| validation | BTC/USDT | HIGH_VOLATILITY | 3 | 66.67 | 0.270 |
| validation | BTC/USDT | LOW_VOLATILITY | 5 | 20.00 | -0.381 |
| validation | BTC/USDT | RANGE | 73 | 38.36 | -0.256 |
| validation | BTC/USDT | TREND_UP | 25 | 52.00 | 0.700 |
| validation | ETH/USDT | HIGH_VOLATILITY | 5 | 20.00 | -1.742 |
| validation | ETH/USDT | RANGE | 73 | 27.40 | -0.346 |
| validation | ETH/USDT | TREND_DOWN | 3 | 33.33 | -0.700 |
| validation | ETH/USDT | TREND_UP | 18 | 38.89 | -0.286 |

## Limits

Small samples, overlapping trades and correlated indicators make these statistics exploratory.
Scanning many correlations creates multiple-comparison risk. Validation is now inspected for descriptive analysis;
using these findings to select future features would consume validation for selection, not final evaluation.
Actual-trade selection is conditional on baseline signals and execution; these rows do not represent every market candle.
Missing first-passage labels are explicitly ambiguous/censored, not losses. No unknown outcome is imputed.
Raw ATR is price-scale dependent, so pooled relationships can be confounded by pair; pair-specific distributions are saved.
No 2025+ outcomes, consumed test or sealed shadow data were loaded. See README.md for exact timing and excursion caveats.

The only near-perfect feature redundancy is body_ratio versus return_1h in both splits
(r approximately 1): hourly candle opens closely match prior closes. Both are
causal, so this is redundancy rather than evidence of future-outcome leakage.
No predictor was removed or selected using this finding.

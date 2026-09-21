# Phase 3A conservative benchmark

Development-frozen candidate: logistic / A_all; primary threshold 0.50.
PR-AUC is average precision, not trapezoidal interpolation. Zero-division precision/recall are reported as zero.

## Development mean fold scores and Validation scores (primary target)

| Model | Features | CV ROC | CV AP | Validation ROC | AP | Balanced acc | Precision | Recall | F1 | Brier | ECE |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| dummy | A_all | 0.500 | 0.333 | 0.500 | 0.356 | 0.500 | 0.000 | 0.000 | 0.000 | 0.230 | 0.024 |
| logistic | A_all | 0.627 | 0.492 | 0.448 | 0.333 | 0.480 | 0.308 | 0.164 | 0.214 | 0.279 | 0.190 |
| forest | A_all | 0.553 | 0.408 | 0.462 | 0.323 | 0.492 | 0.200 | 0.014 | 0.026 | 0.246 | 0.155 |
| hist_gradient | A_all | 0.549 | 0.382 | 0.459 | 0.324 | 0.484 | 0.292 | 0.096 | 0.144 | 0.254 | 0.114 |
| dummy | B_reduced | 0.500 | 0.333 | 0.500 | 0.356 | 0.500 | 0.000 | 0.000 | 0.000 | 0.230 | 0.024 |
| logistic | B_reduced | 0.626 | 0.488 | 0.445 | 0.333 | 0.491 | 0.333 | 0.164 | 0.220 | 0.278 | 0.188 |
| forest | B_reduced | 0.546 | 0.393 | 0.463 | 0.345 | 0.509 | 0.500 | 0.041 | 0.076 | 0.246 | 0.113 |
| hist_gradient | B_reduced | 0.549 | 0.382 | 0.458 | 0.324 | 0.484 | 0.292 | 0.096 | 0.144 | 0.254 | 0.114 |
| dummy | C_price | 0.500 | 0.333 | 0.500 | 0.356 | 0.500 | 0.000 | 0.000 | 0.000 | 0.230 | 0.024 |
| logistic | C_price | 0.609 | 0.478 | 0.450 | 0.328 | 0.466 | 0.270 | 0.137 | 0.182 | 0.274 | 0.144 |
| forest | C_price | 0.560 | 0.440 | 0.453 | 0.323 | 0.480 | 0.125 | 0.014 | 0.025 | 0.250 | 0.133 |
| hist_gradient | C_price | 0.555 | 0.395 | 0.512 | 0.384 | 0.494 | 0.333 | 0.110 | 0.165 | 0.244 | 0.113 |
| dummy | D_price_volatility | 0.500 | 0.333 | 0.500 | 0.356 | 0.500 | 0.000 | 0.000 | 0.000 | 0.230 | 0.024 |
| logistic | D_price_volatility | 0.603 | 0.471 | 0.454 | 0.335 | 0.475 | 0.302 | 0.178 | 0.224 | 0.275 | 0.164 |
| forest | D_price_volatility | 0.560 | 0.416 | 0.469 | 0.343 | 0.508 | 0.444 | 0.055 | 0.098 | 0.249 | 0.109 |
| hist_gradient | D_price_volatility | 0.570 | 0.443 | 0.490 | 0.349 | 0.498 | 0.348 | 0.110 | 0.167 | 0.248 | 0.138 |
| dummy | E_no_regime | 0.500 | 0.333 | 0.500 | 0.356 | 0.500 | 0.000 | 0.000 | 0.000 | 0.230 | 0.024 |
| logistic | E_no_regime | 0.612 | 0.476 | 0.451 | 0.339 | 0.482 | 0.318 | 0.192 | 0.239 | 0.280 | 0.174 |
| forest | E_no_regime | 0.539 | 0.391 | 0.469 | 0.327 | 0.499 | 0.333 | 0.027 | 0.051 | 0.246 | 0.092 |
| hist_gradient | E_no_regime | 0.535 | 0.384 | 0.476 | 0.335 | 0.501 | 0.360 | 0.123 | 0.184 | 0.252 | 0.160 |

## Frozen candidate economics

Subset of actual baseline trades, not a new Freqtrade backtest. No compounding or replacement opportunities.
Drawdown uses closed subset profits on a 1,000-USDT starting basis, not mark-to-market wallet drawdown.

| Split | Threshold | Selected | Retained % | Win % | Net USDT | Avg trade % | PF | Expectancy USDT | DD % | BTC USDT | ETH USDT |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| development_oof | unfiltered | 166 | 100.000 | 31.928 | -7.421 | -0.045 | 0.950 | -0.045 | 4.644 | -18.820 | 11.400 |
| development_oof | 0.5 | 41 | 24.699 | 39.024 | 21.179 | 0.516 | 1.774 | 0.517 | 0.823 | -3.998 | 25.177 |
| development_oof | 0.55 | 31 | 18.675 | 41.935 | 16.625 | 0.536 | 1.982 | 0.536 | 0.701 | -3.913 | 20.539 |
| development_oof | 0.6 | 21 | 12.651 | 42.857 | 5.959 | 0.283 | 1.493 | 0.284 | 0.480 | 0.029 | 5.931 |
| development_oof | 0.65 | 12 | 7.229 | 50.000 | 7.974 | 0.664 | 2.835 | 0.665 | 0.306 | 2.971 | 5.003 |
| development_oof | 0.7 | 7 | 4.217 | 57.143 | 5.811 | 0.830 | 4.930 | 0.830 | 0.125 | 4.030 | 1.781 |
| validation | unfiltered | 205 | 100.000 | 35.610 | -43.445 | -0.212 | 0.842 | -0.212 | 9.155 | -2.283 | -41.162 |
| validation | 0.5 | 39 | 19.024 | 30.769 | -29.693 | -0.763 | 0.435 | -0.761 | 3.429 | -19.028 | -10.665 |
| validation | 0.55 | 32 | 15.610 | 31.250 | -31.562 | -0.988 | 0.290 | -0.986 | 3.156 | -19.854 | -11.708 |
| validation | 0.6 | 25 | 12.195 | 24.000 | -30.141 | -1.207 | 0.187 | -1.206 | 3.014 | -12.696 | -17.445 |
| validation | 0.65 | 14 | 6.829 | 21.429 | -18.888 | -1.350 | 0.238 | -1.349 | 1.927 | -5.962 | -12.926 |
| validation | 0.7 | 11 | 5.366 | 27.273 | -10.862 | -0.987 | 0.352 | -0.987 | 1.264 | -2.253 | -8.609 |

Regime counts for every threshold are in economics.json and economics.csv; all candidates and secondary targets are retained there.

## Metric leaders (descriptive, not post-validation selection)

- development_cv roc_auc: logistic / A_all = 0.6266.
- development_cv pr_auc_ap: logistic / A_all = 0.4917.
- development_cv balanced_accuracy: logistic / D_price_volatility = 0.5904.
- development_cv precision: logistic / C_price = 0.6571.
- development_cv recall: logistic / D_price_volatility = 0.3026.
- development_cv f1: logistic / D_price_volatility = 0.3427.
- development_cv brier: logistic / C_price = 0.2259.
- development_cv ece_5_bins: dummy / A_all = 0.1168.
- validation roc_auc: hist_gradient / C_price = 0.5124.
- validation pr_auc_ap: hist_gradient / C_price = 0.3840.
- validation balanced_accuracy: forest / B_reduced = 0.5092.
- validation precision: forest / B_reduced = 0.5000.
- validation recall: logistic / E_no_regime = 0.1918.
- validation f1: logistic / E_no_regime = 0.2393.
- validation brier: dummy / A_all = 0.2299.
- validation ece_5_bins: dummy / A_all = 0.0243.

## Feature importance stability

Held-out Development AP drop from permuting whole approximately weekly blocks; three repeats.
Negative drops mean the perturbed feature performed better. Correlated features can mask each other.
Permutation changes cross-feature relationships and is descriptive, not a causal intervention.

- forest/A_all: fold rank agreement -0.192; top mean drops: volume_trend_24_168 (+0.012), return_12h (+0.011), return_72h (+0.008).
- forest/B_reduced: fold rank agreement -0.057; top mean drops: distance_high_168 (+0.029), volume_trend_24_168 (+0.003), return_6h (+0.002).
- forest/C_price: fold rank agreement 0.126; top mean drops: return_12h (+0.033), body_to_range (+0.028), close_location (+0.021).
- forest/D_price_volatility: fold rank agreement 0.187; top mean drops: body_to_range (+0.031), return_12h (+0.023), close_location (+0.011).
- forest/E_no_regime: fold rank agreement -0.018; top mean drops: distance_high_168 (+0.018), volume_trend_24_168 (+0.007), body_to_range (+0.004).
- hist_gradient/A_all: fold rank agreement -0.286; top mean drops: candles_since_prior_signal (+0.018), range_ratio (+0.009), day_of_week (+0.006).
- hist_gradient/B_reduced: fold rank agreement -0.107; top mean drops: distance_high_168 (+0.032), regime_duration (+0.011), day_of_week (+0.007).
- hist_gradient/C_price: fold rank agreement -0.045; top mean drops: distance_low_168 (+0.024), distance_high_168 (+0.010), candles_since_prior_signal (+0.009).
- hist_gradient/D_price_volatility: fold rank agreement 0.039; top mean drops: distance_low_168 (+0.044), volatility_percentile_720 (+0.032), body_to_range (+0.029).
- hist_gradient/E_no_regime: fold rank agreement 0.223; top mean drops: distance_low_168 (+0.019), body_ratio (+0.017), distance_high_168 (+0.015).
- logistic/A_all: fold rank agreement 0.094; top mean drops: body_to_range (+0.060), trend_efficiency_20 (+0.037), return_12h (+0.031).
- logistic/B_reduced: fold rank agreement 0.081; top mean drops: regime_duration (+0.045), distance_high_168 (+0.040), body_to_range (+0.037).
- logistic/C_price: fold rank agreement -0.023; top mean drops: body_to_range (+0.071), trend_efficiency_20 (+0.039), return_12h (+0.025).
- logistic/D_price_volatility: fold rank agreement -0.041; top mean drops: body_to_range (+0.051), trend_efficiency_20 (+0.024), return_12h (+0.024).
- logistic/E_no_regime: fold rank agreement -0.071; top mean drops: body_to_range (+0.053), trend_efficiency_20 (+0.018), return_24h (+0.016).

Logistic coefficients are per training-fold standardized numeric feature or training-fitted one-hot category.
Coefficient mean/std/min/max are saved separately; impurity importance is supplementary only.

## Regime ablation (all features minus no-regime)

| Model | CV AP delta | Validation AP delta | Validation ROC delta |
| --- | ---: | ---: | ---: |
| dummy | +0.0000 | +0.0000 | +0.0000 |
| logistic | +0.0158 | -0.0060 | -0.0032 |
| forest | +0.0167 | -0.0037 | -0.0070 |
| hist_gradient | -0.0015 | -0.0104 | -0.0177 |

## Frozen candidate by pair

| Pair | n | ROC | AP | Precision | Recall | Brier |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| BTC/USDT | 106 | 0.423 | 0.405 | 0.348 | 0.182 | 0.297 |
| ETH/USDT | 99 | 0.451 | 0.274 | 0.250 | 0.138 | 0.260 |

## Frozen candidate uncertainty

500 paired calendar-month block resamples; within-month rows retained; only12 blocks, approximate descriptive uncertainty, cross-month dependence not fully represented

- roc_auc: 95% percentile interval [0.3728, 0.5236].
- pr_auc_ap: 95% percentile interval [0.2577, 0.4366].
- brier: 95% percentile interval [0.2493, 0.3107].
- profit_delta_vs_unfiltered: 95% percentile interval [-84.9029, 105.3994].

Intervals condition on the Development selection and do not correct for trying multiple candidates.
Only twelve calendar-month blocks exist; cross-month dependence and selection uncertainty limit inference.
No IID trade bootstrap was used. No drawdown confidence interval is claimed.

## Full outputs

All three targets, every fixed model and every feature set are in results/. Calibration bins and confusion matrices
are retained in per-fold and Validation metrics JSON. Threshold economics includes BTC/ETH and regime distributions.
A higher score or a reduction in losses caused by abstention does not alone establish a tradable edge.
The consumed final test and sealed shadow were never opened. No Freqtrade strategy integration occurred.

## Review conclusion

No stable predictive or tradable edge is demonstrated. The frozen logistic/all
candidate deteriorates from mean Development ROC 0.627 and AP 0.492 to Validation
ROC 0.448 and AP 0.333, below the dummy AP 0.356. Validation calibration is poor
(Brier 0.279, ECE 0.190 versus dummy 0.230 and 0.024). At 0.50, filtering reduces
absolute loss from -43.445 to -29.693 USDT while retaining only 19% of trades.
Average loss worsens from -0.212 to -0.763% per trade and PF from 0.842 to 0.435.
At the same retention fraction, proportional baseline exposure would lose about
8.265 USDT; this is a descriptive exposure benchmark, not a new executable strategy.
The 95% paired month-block interval for profit improvement includes zero widely
(-84.903 to +105.399 USDT). Every frozen candidate threshold loses money in 2024.

Retrospective Validation leaders differ by metric and were NOT substituted for
the frozen candidate. HGB/price has ROC 0.512 and AP 0.384, but these weak,
post-comparison scores do not justify adopting it or selecting thresholds on 2024.

The frozen candidate's ROC is below 0.5 for both BTC (0.423) and ETH (0.451).
Its 0.50 filter makes BTC worse (-19.028 vs -2.283 USDT) and reduces ETH absolute
loss (-10.665 vs -41.162), with much lower exposure. This shows economically
different pair outcomes, not statistically established predictive differences.

Regime features add modest Development AP for logistic/forest but lower Validation
AP for all three learned models. They add no stable measured benefit here.
Permutation rank agreement across folds is weak (logistic/all 0.094; forest/all
-0.192; HGB/all -0.286). Importance is unstable; occasional robust-looking
features do not warrant selection from this small benchmark. Early fold sample
size 50, dozens of features, changing winner identities, strong CV-to-Validation
deterioration and poor calibration are substantial overfitting/nonstationarity
warning signs. No strategy integration or threshold revision is recommended from
these results.

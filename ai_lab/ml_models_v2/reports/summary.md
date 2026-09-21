# Phase 3C review

The larger dataset produces more encouraging development evidence, especially for conservative logistic regression,
but it does not establish deployable ML. All 2019–2024 years are observed development evidence; there is no pristine holdout result.

## Exact chronological folds

| Evaluation | Train rows | Evaluation rows | Purged | Right-edge exclusions |
| ---: | ---: | ---: | ---: | ---: |
| 2020 | 221 | 208 | 2 | 2 |
| 2021 | 431 | 201 | 2 | 2 |
| 2022 | 634 | 210 | 2 | 3 |
| 2023 | 845 | 216 | 4 | 1 |
| 2024 | 1065 | 203 | 1 | 2 |

The 48-hour embargo and label-end purge are applied from the frozen Phase 3B row-ID manifests.

## Primary target: all-feature fold results

| Year | Model | ROC-AUC | PR-AUC | Balanced accuracy | Brier | ECE |
| ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 2020 | dummy | 0.500 | 0.380 | 0.500 | 0.239 | 0.059 |
| 2020 | forest | 0.610 | 0.476 | 0.500 | 0.229 | 0.039 |
| 2020 | hist_gradient | 0.580 | 0.415 | 0.490 | 0.238 | 0.059 |
| 2020 | logistic | 0.580 | 0.465 | 0.529 | 0.237 | 0.056 |
| 2021 | dummy | 0.500 | 0.393 | 0.500 | 0.240 | 0.043 |
| 2021 | forest | 0.607 | 0.488 | 0.525 | 0.231 | 0.021 |
| 2021 | hist_gradient | 0.554 | 0.440 | 0.549 | 0.241 | 0.060 |
| 2021 | logistic | 0.576 | 0.461 | 0.565 | 0.265 | 0.122 |
| 2022 | dummy | 0.500 | 0.305 | 0.500 | 0.215 | 0.060 |
| 2022 | forest | 0.621 | 0.391 | 0.496 | 0.207 | 0.045 |
| 2022 | hist_gradient | 0.556 | 0.402 | 0.531 | 0.215 | 0.057 |
| 2022 | logistic | 0.632 | 0.395 | 0.502 | 0.207 | 0.043 |
| 2023 | dummy | 0.500 | 0.333 | 0.500 | 0.222 | 0.016 |
| 2023 | forest | 0.501 | 0.321 | 0.486 | 0.236 | 0.094 |
| 2023 | hist_gradient | 0.479 | 0.315 | 0.472 | 0.240 | 0.115 |
| 2023 | logistic | 0.549 | 0.351 | 0.493 | 0.230 | 0.098 |
| 2024 | dummy | 0.500 | 0.360 | 0.500 | 0.231 | 0.015 |
| 2024 | forest | 0.606 | 0.452 | 0.502 | 0.225 | 0.023 |
| 2024 | hist_gradient | 0.599 | 0.449 | 0.530 | 0.225 | 0.023 |
| 2024 | logistic | 0.539 | 0.443 | 0.540 | 0.234 | 0.073 |

## Across-year classification summary: all features

| Model | Mean ROC-AUC | Worst ROC-AUC | Mean PR-AUC | Mean Brier | Years ROC > 0.5 | Years AP > Dummy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| dummy | 0.500 | 0.500 | 0.354 | 0.230 | 0/5 | 0/5 |
| forest | 0.589 | 0.501 | 0.426 | 0.225 | 5/5 | 4/5 |
| hist_gradient | 0.554 | 0.479 | 0.404 | 0.232 | 4/5 | 4/5 |
| logistic | 0.575 | 0.539 | 0.423 | 0.235 | 5/5 | 5/5 |

## Logistic feature-set comparison

| Feature set | Mean ROC-AUC | Worst ROC-AUC | Mean PR-AUC | Mean Brier | AP beats Dummy |
| --- | ---: | ---: | ---: | ---: | ---: |
| A_all | 0.575 | 0.539 | 0.423 | 0.235 | 5/5 |
| B_reduced | 0.580 | 0.543 | 0.431 | 0.233 | 5/5 |
| C_price_trend | 0.558 | 0.478 | 0.405 | 0.230 | 4/5 |
| D_price_trend_volatility | 0.582 | 0.540 | 0.419 | 0.228 | 5/5 |
| E_all_excluding_regime | 0.569 | 0.523 | 0.414 | 0.231 | 5/5 |
| F_all_excluding_calendar | 0.575 | 0.544 | 0.419 | 0.235 | 5/5 |

## Prespecified 0.55 threshold: all-feature logistic economics

| Year | Trades | Retained | Win rate | Net USDT | Avg trade | Profit factor | Drawdown | BTC | ETH |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2020 | 14 | 6.7% | 64.3% | 35.400 | 2.527% | 4.675 | 0.773% | 5.373 | 30.027 |
| 2021 | 51 | 25.4% | 51.0% | 36.173 | 0.709% | 1.461 | 1.697% | 34.015 | 2.158 |
| 2022 | 9 | 4.3% | 44.4% | 2.372 | 0.266% | 1.187 | 0.754% | 1.469 | 0.903 |
| 2023 | 3 | 1.4% | 33.3% | -8.682 | -2.897% | 0.001 | 0.869% | -5.179 | -3.502 |
| 2024 | 4 | 2.0% | 75.0% | 4.776 | 1.195% | 3.464 | 0.193% | 0.372 | 4.404 |

Aggregate: 81 trades (7.8% retained), 70.039 USDT, median year 4.776, worst year -8.682, 4/5 profitable years. This threshold was prespecified; it was not selected after seeing these years.

## Pair classification

| Model | Pair | Mean ROC-AUC | Mean PR-AUC | Mean Brier |
| --- | --- | ---: | ---: | ---: |
| dummy | BTC/USDT | 0.500 | 0.354 | 0.230 |
| dummy | ETH/USDT | 0.500 | 0.354 | 0.229 |
| forest | BTC/USDT | 0.578 | 0.413 | 0.227 |
| forest | ETH/USDT | 0.599 | 0.457 | 0.223 |
| hist_gradient | BTC/USDT | 0.538 | 0.390 | 0.234 |
| hist_gradient | ETH/USDT | 0.568 | 0.446 | 0.229 |
| logistic | BTC/USDT | 0.583 | 0.426 | 0.232 |
| logistic | ETH/USDT | 0.572 | 0.449 | 0.237 |

## Stability and interpretation

Logistic coefficient fold-rank stability for all features: median 0.722; minimum 0.426.
Block-permutation importance median year-rank correlation: logistic -0.069, forest 0.128, hist-gradient 0.084.
Those near-zero correlations show unstable explanatory structure despite better average predictions.

The expanded sample improves development evidence relative to Phase 3A: all-feature logistic ROC-AUC exceeds 0.5 in all five folds
and PR-AUC exceeds the contemporaneous Dummy in all five. Forest does so in four years; 2023 remains weak.
Several prespecified logistic thresholds improve pooled economics and four of five years, but rows and labels overlap,
importance is unstable, and no untouched holdout was evaluated. This is evidence worth preserving, not enough to integrate ML into trading.

## Required conclusions

1. Expansion from 422 to 1,271 examples improves the development evidence: logistic ROC-AUC and PR-AUC beat Dummy in every annual fold.
2. Logistic is the most consistent ranker. Forest is competitive and better calibrated on average, but misses Dummy PR-AUC in 2023. Hist-gradient is less stable.
3. Logistic beats Dummy classification across multiple years; its all-feature mean Brier score is worse than Dummy, so probability calibration does not improve consistently.
4. The prespecified logistic 0.55 threshold is profitable in four years and improves net P/L versus the unfiltered baseline in three years. It worsens 2020 and 2023.
5. Economic gains are not confined to one year, but much of the benefit comes from avoiding losses in 2021 and 2022; only 81 trades are retained.
6. BTC and ETH are not materially contradictory. Logistic mean ROC-AUC is 0.583 for BTC and 0.572 for ETH; ETH has higher PR-AUC because its fold prevalence/ranking differs.
7. Regime fields add small average logistic value (ROC-AUC +0.007, PR-AUC +0.009 versus exclusion), but the gain is too small and unstable to call decisive. Calendar exclusion is essentially neutral.
8. Calibration varies by year. Logistic coefficient ranks are moderately stable, while time-block permutation ranks are near zero across years; explanatory importance is not stable.
9. Nonstationarity and overfitting risk remain clear: 2023 is weak, calibration shifts, feature importance changes, labels overlap, and all years have informed development.
10. There is not enough evidence to integrate ML into the strategy. The evidence supports preserving a frozen candidate for a later genuinely sealed evaluation.

Complete results are in fold-metrics.json, prediction-calibration-by-year.json, primary-economic-yearly.csv,
primary-economic-aggregate.csv, and pair-classification-metrics.csv. Secondary-target results remain in the full result files.

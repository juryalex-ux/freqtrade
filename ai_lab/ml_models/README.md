# Phase 3A: conservative frozen time-series benchmark

No strategy changes, integration, live trading, neural networks or hyperparameter
search. Only the 2023 Development and 2024 Validation datasets and corresponding
baseline trade outcomes are read. Neither the consumed test nor shadow is opened.

## Protocol

Three expanding calendar folds train from January 2023 and evaluate Apr–Jun,
Jul–Sep and Oct–Dec 2023. All pairs share the boundaries. Training rows whose
outcome is not complete before the next evaluation window are purged. Test
quarters do not overlap. Indicators may contain earlier price history, but no
training outcomes overlap a future test entry. Fold metrics are equally weighted;
Development economics pools the 166 out-of-fold trades, not the first quarter.

Each target benchmarks the same four fixed configurations across five feature
sets: 20 comparisons per target, 60 in total. This is already substantial relative
to sample size; a CV winner may be a selection artifact. No adaptive search occurs.

- DummyClassifier(strategy=prior): learns the training prevalence.
- LogisticRegression: default L2, C=0.1, lbfgs, max_iter=2000.
- RandomForest: 100 trees, depth<=3, min_samples_leaf=15, sqrt feature sampling,
  bootstrap=False, fixed seed. Trees see chronological training data only.
- HistGradientBoosting: 60 iterations, learning_rate=0.05, depth<=3, <=7 leaves,
  min_samples_leaf=15, l2_regularization=10. Early stopping disabled because its
  default internal validation split is random; fixed iteration count avoids that.

All numeric scaling and category encoding occur inside a Pipeline fitted on
training rows only. OneHotEncoder ignores unseen categories without refitting.
No class reweighting, calibration fitting, outcome transformations or imputation.
The feature whitelist excludes all outcomes, row identifiers and exit timestamps.

## Feature comparisons

- A: all 40 Phase 2C features.
- B: remove body_ratio (near duplicate return_1h), atr14 (price-scale dependent
  analogue of normalized ATR), macd_hist_ratio (exact difference of the two MACD
  components), source_synthetic (constant zero in Development examples).
- C: price/trend features and pair; excludes volume, regime, RSI/MACD and calendar
  features. Pair is retained as context in every set.
- D: C plus ATR, normalized ATR, 24/168-hour return standard deviation and trailing
  volatility percentile. Candle range remains in price/candle features in C.
- E: A excluding regime label, duration and transition.

Exact column lists and every estimator parameter are serialized to protocol.json
before fitting. Removed features are not selected based on Validation performance.

## Freezing and interpretation

All five thresholds (0.50, 0.55, 0.60, 0.65, 0.70) are predeclared. The primary
threshold is fixed at 0.50, not chosen by maximum profits. Higher thresholds are
sensitivity reports, never Validation-selected alternatives. The primary-target
candidate with maximum mean Development-fold average precision is frozen before
Validation is loaded (tie-break: lower Brier). All models are then refit on 2023
only and evaluated once on 2024. frozen-selection.json records that decision.
The benchmark refuses to rerun after results/validation_consumed.json exists.
Do not delete the marker to adapt the benchmark to 2024 results.

2024 was descriptively inspected during Phase 2B/2C. It is a frozen model
evaluation period for this benchmark, not a historically untouched holdout.
No prediction or economic feedback from 2024 is used to choose this benchmark's
configurations, feature removals, candidate or threshold. Reporting retrospective
metric leaders does not select a replacement for the frozen candidate.

Metrics: ROC-AUC; PR-AUC reported as average precision; balanced accuracy,
precision, recall and F1 at 0.50; raw Brier score; five fixed-bin calibration
reliability and ECE; confusion matrix [[TN,FP],[FN,TP]]. Empty-positive precision
is zero by convention. Secondary targets use the same fixed protocol, not new
optimization. Full per-fold and Validation outputs retain weak metrics too.

Economics filters actual historical baseline trades using predicted probability.
It does not simulate replacement opportunities, changed capital availability,
execution or a new strategy. Profits are exact net USDT from original exports;
return contribution uses the original 1,000 USDT. Drawdown is hypothetical closed
subset equity, not original wallet/intratrade drawdown. Empty selections have
zero profit/drawdown and undefined PF/expectancy; avoiding losing trades by taking
none does not establish a tradable edge. Improvement must include economic results
versus the same period's unfiltered baseline; classification gains alone fail.

## Uncertainty and feature importance

Only the Development-frozen candidate gets 95% percentile intervals from 500
paired calendar-month block resamples of Validation. Within-month observations
stay together. Twelve blocks are few; cross-month dependence is not fully captured,
and intervals condition on selection without correcting multiple comparisons.
No IID trade bootstrap or drawdown CI is used.

For the primary target, all nondummy models/feature sets receive held-out-fold
permutation importance: permute whole approximately seven-day row blocks, three
repeats, score by drop in AP. Coefficients and supplementary forest impurity
importance are also saved. Reports compare signed importance and rank stability
across the three folds. These are not causal effects, especially with correlated
features or disrupted cross-feature relationships. No Validation importance is
used for selection.

## Run and artifacts

Use the project `.venv` from the repository root:

```powershell
.venv/Scripts/python.exe -B ai_lab/ml_models/test_protocol.py
.venv/Scripts/python.exe -B ai_lab/ml_models/benchmark.py
.venv/Scripts/python.exe -B ai_lab/ml_models/report.py
```

The repository's requirements-hyperopt.txt provided the exact scikit-learn pin;
it was installed through that official requirements file. Optuna and other listed
dependencies were installed but are not used for tuning. pip check passed.
Do not use Python -O because assertions enforce invariants.

results/ holds predictions, all metrics/calibration/confusion matrices, economics,
importance, tests, installation records and uncertainty. reports/comparison.md
is the human-readable comparison. reports/file-inventory.txt lists exact files.
No prior lab files or core code are modified; the project venv gains dependencies.

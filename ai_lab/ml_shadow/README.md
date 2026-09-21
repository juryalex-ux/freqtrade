# Phase 3D: frozen single-shot shadow evaluation

The user specified the Phase 3C reduced-feature LogisticRegression candidate,
primary target profitable_after_fees, C=0.1 L2 regularization and threshold 0.55.
The original Phase 3C pipeline is imported unchanged. No alternate model,
threshold, feature set, calibration, regime definition or strategy is evaluated.

The freeze records exact features, parameters, preprocessing, input/code hashes,
Git commit plus uncommitted source hashes, UTC time, fees, attribution and
decision criteria. The pipeline is fitted on all 1,271 development trades in
2019-2024 and serialized before any shadow file is accessed. Fitting before
unsealing provides a stronger isolation boundary than fitting after unsealing.
Training never reads 2025 or 2026 rows. March 2026 data initializes the unchanged
causal feature pipeline only; it is excluded from fitting and scoring.

Shadow interval: 2026-04-01 inclusive through 2026-09-01 exclusive, UTC. Original
seal and prices remain byte-for-byte unchanged. CONSUMED.json in this folder
supersedes the historical SEALED_UNEVALUATED status; it does not alter/reseal the
original evidence. All future phases must treat the shadow as consumed.

Economic attribution is a subset of actual frozen LabBaseline portfolio trades.
This does not simulate additional entries unlocked by filtering. Fee is 0.1%
each side, already included in the exported net outcomes; stake 100 USDT, wallet
1,000 USDT. Subset drawdown uses close-time realized equity and simultaneous
closes; it does not measure intratrade risk. Phase 3C's code actually ordered
P/L by entry-day despite its README claiming close-day. This metric discrepancy
is corrected explicitly here and recorded before unsealing; trading and
attribution rules do not change. Consecutive losses use close time, then pair
as the deterministic same-time tie-breaker. Classification and economics use
the frozen 0.55 cutoff. The Phase 3C standard 0.50 classification metrics are
retained separately for compatibility; there is no alternative economic threshold.

The category criteria in frozen-candidate.json are conservative operational
review criteria, not significance tests. No IID confidence interval is claimed.
All metrics are descriptive with overlapping market exposure and limited trades.

Run once, in this order, from the repository root:

```powershell
.venv/Scripts/python.exe -B ai_lab/ml_shadow/test_protocol.py
.venv/Scripts/python.exe -B ai_lab/ml_shadow/freeze.py
.venv/Scripts/python.exe -B ai_lab/ml_shadow/evaluate.py
```

Freeze and evaluation refuse to overwrite prior start/consumption artifacts.
Technical failures remain in audit.jsonl and must not motivate changed settings.
The complete baseline console output and command are retained under backtest/.

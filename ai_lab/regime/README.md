# Phase 2B: causal descriptive regime analysis

This is a detector and attribution report, not a strategy or a regime filter.
LabBaseline is unchanged. No FreqAI, ML, fitting, search or optimization is used.
Only 2023 Development and 2024 Validation trade results are loaded. The consumed
Apr 2025–Mar 2026 test is not loaded by any analysis code.

## Fixed thresholds and rationale

These are simple a-priori hourly heuristics, declared in specification.json before
performance was calculated. They are not calibrated optimal values or universally
valid market definitions. No threshold was changed in response to results.

| Indicator | Definition / threshold | Rationale |
| --- | --- | --- |
| Fast/slow EMA | 20 / 50 hours, causal adjust=False EMA | Roughly one/two trading days; a small fixed trend scale |
| Slow EMA slope | Current EMA50 versus six hours earlier | Require persistent direction rather than an instantaneous crossover |
| EMA separation | (EMA20 − EMA50) / close, magnitude at least 0.2% | Reject nearly touching averages |
| Efficiency | Absolute 20-hour net price change / sum of absolute hourly changes, at least 0.30 | Require at least 30% directional efficiency; an explainable trend-strength alternative to ADX |
| Normalized ATR | True range EMA with alpha=1/14, divided by current close | Scale candle range by price; same rule for BTC and ETH |
| High volatility | Normalized ATR >= 1.5% | Fixed elevated hourly-range heuristic |
| Low volatility | Normalized ATR <= 0.3% | Fixed compressed hourly-range heuristic |
| Warmup | 200 candles | About four slow-EMA spans; data begins Dec 1, 2022 so both scored periods have sufficient history |

Mutually exclusive precedence: HIGH_VOLATILITY, LOW_VOLATILITY, TREND_UP,
TREND_DOWN, otherwise RANGE. Trend labels require sufficient efficiency, signed
EMA separation and matching slope. Volatility overrides trend, so RANGE means
neither a volatility extreme nor a sufficiently strong directional trend.
ATR initialization uses the first candle's high-low; all smoothing is past-only.
No centered windows, negative shifts, future return labels, global percentiles or
whole-sample scaling are used. Warmup has no valid label rather than a fake regime.

## Timing and data

A candle stamped t is known only at t+1h. Trades at entry t use the label of the
candle stamped t−1h. The same-hour high/low/close is never used to label an entry.
Calendar distributions describe candle-close labels; trade attribution describes
what was available at entry. Validation continues indicator state from past data;
no future data contributes to state. Both periods are UTC and end-exclusive.

The known Binance gap at 2023-03-24 13:00 UTC is explicitly checked, then filled
using the last available close for OHLC and zero volume, matching Phase 2A's policy.
The synthetic flag is retained. Duplicate and unexpected missing timestamps fail.
The fill affects indicators and is disclosed, not treated as a real observation.

## Metrics and interpretation

Return contribution = sum of the regime's exported trade net profits / original
1,000 USDT wallet. Pair contributions use that same wallet basis. Average trade
is the mean exported per-trade percentage; expectancy is mean net USDT per trade.
Profit factor is positive profits divided by absolute losses. No losing trades
produces null PF with an explanation; empty categories are retained explicitly.

Drawdown is the maximum decline of a hypothetical closed-trade equity curve for
that subset, initialized at 1,000 USDT and aggregating simultaneous closes. It is
NOT the full strategy's wallet drawdown or intratrade mark-to-market risk. Average
duration is in hours. Exits include boundary force exits from original backtests.
Fees are already in exported net trade profits; no fees are subtracted twice.
Per-regime profits and counts reconcile to the unchanged Development/Validation
backtests. A favorable subset is not proof that trading only it would reproduce
these results: capital constraints, opportunities and selection effects differ.
Small categories are descriptive evidence only. No trading rule recommendations
or optimized thresholds are produced.

## Files and running

From the repository root, with the project environment:

```powershell
.venv/Scripts/python.exe -B ai_lab/regime/test_detector.py
.venv/Scripts/python.exe -B ai_lab/regime/analyze.py
.venv/Scripts/python.exe -B ai_lab/regime/report.py
```

`detector.py` implements batch and independent streaming calculations.
`results/` contains label CSVs, attributed trades, distributions, per-regime and
per-pair metrics, exit breakdowns, hashes, tests and audit outputs.
`reports/comparison.md` is the human-readable report.
`reports/file-inventory.txt` lists every created file.

## Sealed shadow holdout

`shadow/SEALED.json` hashes the two timestamp-trimmed 1h files for
2026-04-01 inclusive through 2026-09-01 exclusive. `seal_shadow.py` only downloads,
checks timestamps and hashes files. It never imports this detector or any strategy,
and refuses to overwrite an existing seal. No shadow labels, performance or
strategy results are calculated. The analysis reader is hard-coded to the separate
design-data directory and the two authorized result directories.

The seal is an audit boundary, not encryption or an OS access-control mechanism.
Do not unseal without a separately reviewed later evaluation protocol. Prior
exchange pagination can cache a few boundary candles; 'untouched' means no
performance or regime inspection, not a claim of no historical public-price
knowledge. Initial synthetic testing exposed a None/NaN warmup representation
mismatch; that was fixed before the real performance analysis without changing
any regime threshold.

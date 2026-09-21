# Phase 2A: fixed-strategy chronological evaluation

Run from the repository root using `.venv/Scripts/python.exe -B
ai_lab/evaluation/evaluate.py`. The completed final test is deliberately single-use:
the runner rejects subsequent full runs when `results/test_consumed.json` exists.
Do not delete that marker to reuse the test for selection. Validation tests alone:
`.venv/Scripts/python.exe -B ai_lab/evaluation/test_guards.py`.

`protocol.json` declares dates, hashes and policy before results are observed.
`frozen/lock.json` records the runner/protocol hashes before evaluation; the final
test is downloaded and evaluated only after non-test runs and bias checks succeed.
`results/commands.jsonl` records exact Freqtrade commands and timestamps.
Each run has its own ZIP export, full metrics.json, summary.json, log and data audit.
The original Jan–Mar 2025 ZIP and console output are copied under `frozen/`.

All ranges are UTC and half-open [start, end). The frozen reference was generated
by the earlier runner; it is retained byte-for-byte, not silently recomputed.
2023 is development; 2024 is validation; Apr 2025–Mar 2026 is the final held-out
test. The already-observed Jan–Mar 2025 period is excluded from all primary splits.
There is no random splitting, fitting, optimization or parameter adaptation.

Six walk-forward folds use six calendar months of development followed by three
months of validation, stepping forward three months from Jan 2023. Each run starts
with 1,000 USDT, no positions and the same 100-USDT stake, two-trade limit, 0.1%
fee per side and unchanged strategy. Development means historical evaluation here;
it does not train a model. Development windows intentionally overlap across folds;
validation windows do not. Never pool overlapping development runs as independent
evidence. Fold validation returns are not a continuous compounded portfolio.

Every run receives a physically separate candle slice: only its scoring interval
and 51 immediately preceding hours. No future candles are supplied. Past-only
warmup can cross a preceding split boundary but creates no scored observations
or fitted parameters there. Boundary positions are force-closed independently by
Freqtrade; this reset changes results versus a continuous multi-year portfolio.
The final available hourly candle is end minus one hour, so Freqtrade's reported
last timestamp can precede the protocol's exclusive end by one hour.

Checks cover missing/duplicate/unordered candles, null values, negative volume,
trade timestamp bounds, split overlap, unchanged config/strategy, environment
overrides and branch. Prefix tests compare SMA and signal values with future rows
removed. Freqtrade lookahead-analysis runs on validation only, with its diagnostic
market-order and wallet overrides; these are not strategy parameter changes.

This holdout is unseen by this lab's prior runs, not a guarantee that nobody has
ever examined those historical market prices. After its results are reported it
is consumed. Future AI/ML selection must use development/validation only and needs
a fresh untouched holdout for another final evaluation. Hashes, a single-use marker
and a no-optimization API guard against accidents; they cannot prevent someone from
manually using a published result. Do not run Python with -O (assertions enforce
these checks). These are backtests with current exchange metadata, not realistic
queue/latency/slippage simulation or proof of profitability.

No FreqAI, ML, hyperopt, live trading, core changes or Git writes are included.

A Binance-verified gap at 2023-03-24 13:00 UTC is allowlisted. Freqtrade applies
its standard past-close, zero-volume fill; all other gaps fail. Existing zero-volume
source candles are counted, retained and cannot generate volume-gated signals.
Early pre-test execution failures (path resolution, missing-hour and zero-volume
checks) are retained in execution.log; corrections did not inspect test data or
change strategy parameters.

Holdout provenance limitation: Phase 1 previously cached a few extra April 2025
candles outside its scoring interval. Unseen means not evaluated or used for
parameter selection, not that no raw price was ever downloaded. No external
human knowledge of historical prices can be ruled out.

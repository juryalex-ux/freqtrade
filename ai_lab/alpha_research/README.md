# Phase 4A: causal alpha research, 2019–2022 only

Five independent, deterministic long-only candidate families are frozen in
protocol.json: trend pullback, confirmed breakout, restricted mean reversion,
volatility squeeze breakout, and momentum persistence. Each has a central rule
plus two predefined perturbations of one parameter. No best parameter is selected.
No FreqAI, ML, neural network, strategy combination or optimization is used.

All definitions and acceptance criteria were written before performance was read.
2019–2020 provide initial design context; 2021 is the next-year internal check;
2022 is the next expanding-window internal check. Because rules are deterministic,
there is no fitting or updating between these windows. These historical years
have been used in earlier projects and are not claimed as pristine holdouts.

The downloader obtains only Dec 2018 warmup through Dec 2022. It does not open
the previous mixed-date datasets or any 2023+ result files. All REST requests
have an explicit endTime before Jan 1, 2023, including gap rechecks. Missing
candles are recorded, independently requested, then explicitly filled with prior
close OHLC and zero volume. Real observations are preserved separately.

Execution is official Freqtrade backtesting with 1h Binance spot BTC/USDT and
ETH/USDT, 0.1% fee per side, 100 USDT fixed stake, 1,000 USDT initial wallet,
two positions maximum, unchanged limit-order and engine fill assumptions. Every
year starts with a fresh wallet and past-only warmup; annual force exits remain
in the results. This is annual walk-forward research, not one compounded run.

The original LabBaseline source is never changed. The strategy folder contains
a byte-identical copy solely so the engine can resolve all 16 strategy classes
in one explicitly scoped directory. The copy and original must match the
permanent frozen SHA256. The other 15 classes represent five families times
three nearby settings, not 15 independent alpha families.

All candidates use EMA20/50, 6h EMA slope, efficiency20, ATR14/RSI14, and prior24
mean volume as a small common indicator vocabulary. Exact formulas and each
family's entry/exit rationale are in protocol.json and reports/comparison.md.
No indicator is normalized by future observations or fitted globally. Candle t
is observed when it closes; engine entries occur on the following candle. High/
low reference levels are shifted one candle; prefix and mutation tests cover
both indicator values and entry/exit signals for every variant.

Run from the repository root (freeze and completed backtests refuse overwrite):

```powershell
.venv/Scripts/python.exe -B ai_lab/alpha_research/test_causality.py
.venv/Scripts/python.exe -B ai_lab/alpha_research/freeze.py
.venv/Scripts/python.exe -B ai_lab/alpha_research/download.py
.venv/Scripts/python.exe -B ai_lab/alpha_research/test_causality.py
.venv/Scripts/python.exe -B ai_lab/alpha_research/run.py
.venv/Scripts/python.exe -B ai_lab/alpha_research/report.py
.venv/Scripts/python.exe -B ai_lab/alpha_research/finalize.py
```

All yearly/pair/variant metrics and exit contributions are reported, including
empty/weak cells. Reported Sharpe uses mean/std of a full calendar of daily closed
P/L divided by 1,000, times sqrt365. Sortino uses negative-return RMS including
zero-return days. These are realized-P/L research statistics, not full marked
equity ratios. Engine native Sharpe/Sortino are separate columns. Aggregate net
P/L sums four annually reset runs; aggregate return sums are not compounded.

Candidate continuation is gated by all predeclared protocol checks. No central
candidate is replaced by a favorable nearby setting. Passing is permission for
research consideration only, not authorization to use consumed periods or to
deploy. Failed hypotheses and all evidence remain archived.

Main report: reports/comparison.md. Audit: audit.jsonl and audits/. File inventory:
reports/file-inventory.txt. No commits, push, live trading or core edits.

# Phase 4A deterministic alpha research

Only 2019-2022 outcomes were evaluated. All five candidate definitions, one-parameter neighborhoods and acceptance criteria were frozen before viewing results.
The preceding December supplies warmup only. No consumed-period dataset or performance file is read by this workflow.
2019-2022 were used in earlier research, so these are development results, not a pristine holdout.

## Candidate definitions

### AlphaTrend

Entry: EMA20>EMA50; EMA50 rising over6h; efficiency20>=0.30; prior low<=prior EMA20; current close>EMA20; 3h return>0.

Structural exit: close below EMA50.

Rationale: Buy a recovered pullback in an established efficient uptrend; 0.30 rejects very choppy paths.

Perturbation: {'parameter': 'efficiency_min', 'values': [0.25, 0.3, 0.35]}

### AlphaBreakout

Entry: close above prior24h high+0.1ATR14; NATR above prior24h mean; relative volume>=1.2; close in top25% of candle.

Structural exit: close below prior12h low.

Rationale: One-day breakout with modest volatility/volume expansion and a strong close; buffered close rejects wick-only breakouts but cannot eliminate false breakouts.

Perturbation: {'parameter': 'breakout_window', 'values': [20, 24, 28]}

### AlphaReversion

Entry: close<EMA20-1.5ATR14; RSI14<30; close>prior close; efficiency20<0.25; abs EMA50 six-hour slope<0.005; NATR14<0.015.

Structural exit: close>=EMA20 or RSI14>=50.

Rationale: Volatility-scaled oversold rebound restricted to weak-trend, non-extreme-volatility conditions; cautious entry can yield few trades.

Perturbation: {'parameter': 'stretch_atr', 'values': [1.35, 1.5, 1.65]}

### AlphaSqueeze

Entry: At least one of prior6 candles had BB20 total width(4 population std) < Keltner total width(3ATR14); close breaks prior20h high; NATR rising; relative volume>=1.2.

Structural exit: close below EMA20.

Rationale: Prior compression followed by directional expansion. Prior-only squeeze test avoids calling the breakout itself compression.

Perturbation: {'parameter': 'keltner_multiplier', 'values': [1.35, 1.5, 1.65]}

### AlphaMomentum

Entry: 24h and72h returns positive; up-close fraction24>=0.60; relative volume>=1.2; bullish candle; close in top30%; close above prior6h high.

Structural exit: 24h return<=0 or close below EMA20.

Rationale: Require persistent buying across short/medium horizons, participation and strong candle structure.

Perturbation: {'parameter': 'persistence_min', 'values': [0.55, 0.6, 0.65]}

All candidates also use unchanged baseline-like 5% ROI and -5% stoploss, positive entry volume, first true-condition candle only, and next-candle engine execution. These are isolated strategy classes, not a change to LabBaseline.

## Annual portfolio metrics

| Candidate | Year | Trades | Win % | Return % | Net USDT | Avg trade % | PF | Expectancy | Wallet DD % | Sharpe | Sortino | Duration h | Loss streak |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| LabBaseline | 2019 | 223 | 32.29 | -3.52 | -35.17 | -0.16 | 0.88 | -0.16 | 9.48 | -0.68 | -0.99 | 27.97 | 18 |
| LabBaseline | 2020 | 210 | 38.10 | 6.08 | 60.83 | 0.29 | 1.22 | 0.29 | 5.65 | 1.02 | 1.66 | 30.38 | 11 |
| LabBaseline | 2021 | 203 | 38.92 | -4.84 | -48.37 | -0.24 | 0.87 | -0.24 | 10.11 | -0.71 | -1.00 | 24.33 | 20 |
| LabBaseline | 2022 | 213 | 30.05 | -9.84 | -98.39 | -0.46 | 0.71 | -0.46 | 11.07 | -1.67 | -2.22 | 24.68 | 24 |
| AlphaTrend | 2019 | 85 | 36.47 | 3.72 | 37.18 | 0.44 | 1.40 | 0.44 | 1.93 | 1.17 | 2.35 | 19.80 | 11 |
| AlphaTrend | 2020 | 97 | 29.90 | -1.70 | -16.99 | -0.18 | 0.87 | -0.18 | 5.74 | -0.49 | -0.76 | 19.93 | 14 |
| AlphaTrend | 2021 | 95 | 33.68 | -1.20 | -12.03 | -0.13 | 0.92 | -0.13 | 5.12 | -0.34 | -0.52 | 15.18 | 14 |
| AlphaTrend | 2022 | 69 | 37.68 | 0.38 | 3.81 | 0.06 | 1.04 | 0.06 | 4.42 | 0.13 | 0.20 | 19.75 | 11 |
| AlphaBreakout | 2019 | 123 | 40.65 | -2.77 | -27.73 | -0.23 | 0.88 | -0.23 | 4.36 | -0.68 | -0.99 | 23.77 | 9 |
| AlphaBreakout | 2020 | 143 | 51.75 | 13.95 | 139.47 | 0.97 | 1.84 | 0.98 | 2.31 | 2.61 | 5.63 | 23.78 | 7 |
| AlphaBreakout | 2021 | 124 | 54.03 | 13.51 | 135.06 | 1.09 | 1.96 | 1.09 | 2.01 | 2.81 | 5.76 | 22.69 | 8 |
| AlphaBreakout | 2022 | 95 | 46.32 | 4.02 | 40.22 | 0.42 | 1.34 | 0.42 | 2.48 | 1.09 | 1.91 | 24.92 | 7 |
| AlphaReversion | 2019 | 1 | 100.00 | 0.01 | 0.08 | 0.08 | N/A | 0.08 | 0.20 | 1.00 | N/A | 17.00 | 0 |
| AlphaReversion | 2020 | 1 | 100.00 | 0.10 | 1.00 | 1.00 | N/A | 1.00 | 0.04 | 1.00 | N/A | 18.00 | 0 |
| AlphaReversion | 2021 | 0 | N/A | 0.00 | 0.00 | N/A | N/A | N/A | 0.00 | N/A | N/A | N/A | 0 |
| AlphaReversion | 2022 | 0 | N/A | 0.00 | 0.00 | N/A | N/A | N/A | 0.00 | N/A | N/A | N/A | 0 |
| AlphaSqueeze | 2019 | 198 | 35.35 | 6.25 | 62.51 | 0.32 | 1.33 | 0.32 | 3.98 | 1.15 | 2.66 | 13.17 | 14 |
| AlphaSqueeze | 2020 | 219 | 40.18 | 11.88 | 118.81 | 0.54 | 1.62 | 0.54 | 1.76 | 2.39 | 5.07 | 14.17 | 9 |
| AlphaSqueeze | 2021 | 208 | 40.87 | 6.60 | 65.98 | 0.32 | 1.31 | 0.32 | 2.83 | 1.49 | 2.81 | 13.04 | 11 |
| AlphaSqueeze | 2022 | 188 | 32.45 | -4.35 | -43.54 | -0.23 | 0.79 | -0.23 | 5.63 | -1.15 | -1.69 | 12.54 | 13 |
| AlphaMomentum | 2019 | 100 | 30.00 | -1.10 | -11.02 | -0.11 | 0.92 | -0.11 | 4.16 | -0.34 | -0.57 | 11.39 | 12 |
| AlphaMomentum | 2020 | 134 | 35.07 | -0.14 | -1.40 | -0.01 | 0.99 | -0.01 | 2.97 | -0.03 | -0.06 | 13.13 | 13 |
| AlphaMomentum | 2021 | 114 | 39.47 | -0.29 | -2.88 | -0.03 | 0.98 | -0.03 | 5.49 | -0.07 | -0.12 | 13.25 | 9 |
| AlphaMomentum | 2022 | 66 | 30.30 | -3.46 | -34.60 | -0.52 | 0.52 | -0.52 | 4.80 | -1.77 | -2.18 | 15.89 | 7 |

Sharpe/Sortino here use a full calendar of daily closed P/L divided by a fixed 1000 USDT wallet, annualized sqrt365, with zero-risk-free return. Sortino downside RMS includes zero-return days. Undefined ratios are N/A. Engine-native portfolio ratios are retained separately in yearly-metrics.csv.
Wallet DD is the engine wallet-statistics drawdown. Pair closed-trade DD uses the common1000 USDT basis; do not add pair drawdowns. Annual wallets reset; summed returns are not a compounded strategy return.
Engine timeranges include the next January1 midnight endpoint where present: seven forced exits across the2020/2021 strategy runs close exactly on that boundary. Their exact timestamps are retained and P/L assigned to the preceding final calendar day for daily ratios. No post2022 candles exist in the input;2022 ends Dec31 23:00. Thus yearly runs touch at a boundary point rather than being strictly disjoint; no fitting or parameter adaptation occurs across it.

## Aggregate and pair comparison

| Candidate | Pair | Trades | Net USDT | PF | Positive years | Expectancy USDT |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| LabBaseline | ALL | 849 | -121.09 | 0.91 | 1/4 | -0.14 |
| LabBaseline | BTC/USDT | 420 | -52.18 | 0.91 | 1/4 | -0.12 |
| LabBaseline | ETH/USDT | 429 | -68.91 | 0.90 | 1/4 | -0.16 |
| AlphaTrend | ALL | 346 | 11.97 | 1.03 | 2/4 | 0.03 |
| AlphaTrend | BTC/USDT | 179 | -20.33 | 0.91 | 1/4 | -0.11 |
| AlphaTrend | ETH/USDT | 167 | 32.30 | 1.13 | 4/4 | 0.19 |
| AlphaBreakout | ALL | 485 | 287.02 | 1.44 | 3/4 | 0.59 |
| AlphaBreakout | BTC/USDT | 234 | 109.05 | 1.37 | 3/4 | 0.47 |
| AlphaBreakout | ETH/USDT | 251 | 177.97 | 1.51 | 3/4 | 0.71 |
| AlphaReversion | ALL | 2 | 1.08 | N/A | 2/4 | 0.54 |
| AlphaReversion | BTC/USDT | 1 | 1.00 | N/A | 1/4 | 1.00 |
| AlphaReversion | ETH/USDT | 1 | 0.08 | N/A | 1/4 | 0.08 |
| AlphaSqueeze | ALL | 813 | 203.77 | 1.25 | 3/4 | 0.25 |
| AlphaSqueeze | BTC/USDT | 414 | 68.28 | 1.18 | 3/4 | 0.16 |
| AlphaSqueeze | ETH/USDT | 399 | 135.48 | 1.33 | 3/4 | 0.34 |
| AlphaMomentum | ALL | 414 | -49.90 | 0.91 | 0/4 | -0.12 |
| AlphaMomentum | BTC/USDT | 201 | -25.96 | 0.89 | 2/4 | -0.13 |
| AlphaMomentum | ETH/USDT | 213 | -23.95 | 0.92 | 1/4 | -0.11 |

## Walk-forward evaluation

No fitting or calibration applies to these deterministic rules. After2019-2020 initial-design context,2021 is the next-year check; after2019-2021 context,2022 is the final internal check. Definitions and central values stay frozen, including after2021.

| Candidate | 2021 net | 2021 PF | 2022 net | 2022 PF |
| --- | ---: | ---: | ---: | ---: |
| LabBaseline | -48.37 | 0.87 | -98.39 | 0.71 |
| AlphaTrend | -12.03 | 0.92 | 3.81 | 1.04 |
| AlphaBreakout | 135.06 | 1.96 | 40.22 | 1.34 |
| AlphaReversion | 0.00 | N/A | 0.00 | N/A |
| AlphaSqueeze | 65.98 | 1.31 | -43.54 | 0.79 |
| AlphaMomentum | -2.88 | 0.98 | -34.60 | 0.52 |

## Nearby-parameter robustness

| Candidate | Parameter | Value | Trades | Net USDT | PF | Positive years |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| AlphaTrend | efficiency_min | 0.25 | 481 | -62.60 | 0.90 | 1/4 |
| AlphaTrend | efficiency_min | 0.3 | 346 | 11.97 | 1.03 | 2/4 |
| AlphaTrend | efficiency_min | 0.35 | 219 | 15.75 | 1.05 | 2/4 |
| AlphaBreakout | breakout_window | 20 | 515 | 257.31 | 1.37 | 3/4 |
| AlphaBreakout | breakout_window | 24 | 485 | 287.02 | 1.44 | 3/4 |
| AlphaBreakout | breakout_window | 28 | 463 | 262.67 | 1.42 | 3/4 |
| AlphaReversion | stretch_atr | 1.35 | 2 | 1.08 | N/A | 2/4 |
| AlphaReversion | stretch_atr | 1.5 | 2 | 1.08 | N/A | 2/4 |
| AlphaReversion | stretch_atr | 1.65 | 2 | 1.08 | N/A | 2/4 |
| AlphaSqueeze | keltner_multiplier | 1.35 | 686 | 136.15 | 1.20 | 3/4 |
| AlphaSqueeze | keltner_multiplier | 1.5 | 813 | 203.77 | 1.25 | 3/4 |
| AlphaSqueeze | keltner_multiplier | 1.65 | 894 | 216.79 | 1.24 | 3/4 |
| AlphaMomentum | persistence_min | 0.55 | 635 | -55.87 | 0.93 | 2/4 |
| AlphaMomentum | persistence_min | 0.6 | 414 | -49.90 | 0.91 | 0/4 |
| AlphaMomentum | persistence_min | 0.65 | 213 | 1.75 | 1.01 | 2/4 |

Only the original central settings can continue. A neighbor is never promoted because its result is better. Full yearly and pair metrics for every neighbor are retained.

## Predeclared decisions

- AlphaTrend: reject for continuation; failed checks: positive_expectancy_multiple_years, pf_above_one_multiple_years, not_one_positive_year_dominated, both_pairs_positive, both_neighbors_positive, neighbors_multiple_positive_years.
- AlphaBreakout: eligible to freeze for later evaluation; failed checks: none.
- AlphaReversion: reject for continuation; failed checks: positive_expectancy_multiple_years, pf_above_one_multiple_years, sufficient_total_trades, sufficient_each_year, not_one_positive_year_dominated, internal_2022_positive.
- AlphaSqueeze: reject for continuation; failed checks: internal_2022_positive.
- AlphaMomentum: reject for continuation; failed checks: positive_expectancy_multiple_years, pf_above_one_multiple_years, aggregate_positive, not_one_positive_year_dominated, both_pairs_positive, internal_2022_positive, both_neighbors_positive.

Acceptance requires three positive-expectancy/PF>1 years; aggregate positive;100 trades total and15 each year; max yearly wallet DD<=10%; no year>65% of total positive yearly P/L; both pairs positive;2022 positive; both neighbors positive overall and at least two positive years each.
These rules support research triage, not deployment. No future or consumed-period evaluation is authorized by passing them.

## Exit contributions

| Candidate | Reason | Trades | Net USDT |
| --- | --- | ---: | ---: |
| AlphaBreakout | breakout_exit | 261 | -364.40 |
| AlphaBreakout | roi | 178 | 890.16 |
| AlphaBreakout | stop_loss | 46 | -238.74 |
| AlphaMomentum | momentum_exit | 299 | -319.34 |
| AlphaMomentum | roi | 85 | 425.14 |
| AlphaMomentum | stop_loss | 30 | -155.71 |
| AlphaReversion | reversion_exit | 2 | 1.08 |
| AlphaSqueeze | roi | 173 | 865.15 |
| AlphaSqueeze | squeeze_exit | 627 | -593.89 |
| AlphaSqueeze | stop_loss | 13 | -67.49 |
| AlphaTrend | force_exit | 1 | 3.61 |
| AlphaTrend | roi | 92 | 460.07 |
| AlphaTrend | stop_loss | 21 | -109.03 |
| AlphaTrend | trend_exit | 232 | -342.68 |
| LabBaseline | force_exit | 6 | -2.63 |
| LabBaseline | roi | 214 | 1070.11 |
| LabBaseline | sma_cross_down | 514 | -591.86 |
| LabBaseline | stop_loss | 115 | -596.71 |

## Limitations and artifacts

Hourly OHLCV execution is approximate. Fee is0.1% per side, already in trade outcomes; no additional slippage stress was run. Current exchange market metadata is not historically exact. Explicit gap fills may affect indicators. Annual boundary force exits are included. Small cells and correlated markets limit inference.
Prefix and future-mutation checks test causality; no indicator uses future returns or centered windows. They do not establish an economic edge.
Reports include all yearly/pair/variant metrics, exact commands and complete engine outputs. Full file inventory and hashes are retained. LabBaseline and Freqtrade core remain unchanged.

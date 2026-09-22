# Phase 5A deterministic alpha architecture research

All results use only 2019-01-01 through 2022-12-31, with December 2018 as warmup. No 2023+ data was loaded.

## Frozen definitions

### V2TrendPullback

- Market state: EMA50>EMA200, EMA50 12h slope>=0.3%, efficiency48>=0.25, NATR<=1.5x prior72h mean
- Setup: Within prior 4 candles low touched EMA20 zone, stayed >=98% EMA50, and close retained >=99.5% EMA50
- Trigger: Bullish candle close above prior3h high, positive 3h return, close location>=60%
- Risk: Entry-to-prior6h-low distance 0.35-2.5 ATR; structural damage exit; emergency stop -6%
- Exit: Close below EMA50 or prior10h low; ROI 6%
- Rationale: Require established directional state, a controlled retracement, and observable resumption rather than buying the first breakout.
- Predeclared neighborhood: `{'trend_slope_min': [0.002, 0.003, 0.004]}`

### V2CompressionBreakout

- Market state: EMA50 12h slope>=-0.3% and NATR<=1.8x prior72h mean
- Setup: At least 4 of previous6 candles compressed; BB20 width/(4 ATR14)<=0.80 and NATR below prior72h mean
- Trigger: Close above prior12h compression high+0.05ATR, true range>=1.2x prior ATR, relative volume>=1.15, close location>=75%
- Risk: Entry-to-prior12h-low distance 0.5-2.75 ATR; emergency stop -6%
- Exit: Close below EMA20 or prior12h low; ROI 6%
- Rationale: Demand persistent contraction before participation-backed range expansion and reject structurally wide entries.
- Predeclared neighborhood: `{'compression_ratio_max': [0.75, 0.8, 0.85]}`

### V2RegimeAdaptive

- Market state: Exclusive trend state (EMA50>EMA200, slope>=0.25%, efficiency48>=0.25) else range state (abs slope<0.4%, efficiency24<0.30, NATR<1.2x prior72h mean)
- Setup: Trend: prior4h EMA20 pullback above 98% EMA50. Range: prior close below EMA20-1.35ATR with prior RSI<32
- Trigger: Trend: bullish prior3h-high reclaim. Range: bullish reversal above prior close. Trend owns overlaps, so one candle cannot use both setups
- Risk: Trend distance to prior6h low 0.35-2.5 ATR; range candle recovery <=1.5ATR; emergency stop -6%
- Exit: Close below prior10h low or completed mean reversion (close>=EMA20 and RSI>=50); ROI 6%
- Rationale: Assign exactly one setup to each of two economic states instead of applying one signal across incompatible conditions.
- Predeclared neighborhood: `{'range_stretch_atr': [1.2, 1.35, 1.5]}`

## Annual portfolio results at 0.10% fee per side

| Year | Strategy | Trades | W/L | Win % | Net USDT | Return % | Avg % | PF | Expectancy | Wallet DD % | Sharpe | Sortino | Duration h | Loss streak |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2019 | V2TrendPullback | 43 | 13/30 | 30.23 | 4.31 | 0.43 | 0.10 | 1.07 | 0.10 | 1.74 | 0.06 | 0.15 | 19.63 | 7 |
| 2019 | V2CompressionBreakout | 18 | 2/16 | 11.11 | -8.77 | -0.88 | -0.49 | 0.58 | -0.49 | 1.83 | -0.19 | -0.62 | 8.44 | 13 |
| 2019 | V2RegimeAdaptive | 20 | 11/9 | 55.00 | -5.91 | -0.59 | -0.29 | 0.58 | -0.30 | 0.89 | -0.21 | -0.28 | 8.40 | 2 |
| 2019 | LabBaseline | 223 | 72/151 | 32.29 | -35.17 | -3.52 | -0.16 | 0.88 | -0.16 | 9.25 | -0.60 | -1.17 | 27.97 | 18 |
| 2019 | AlphaBreakout | 123 | 50/73 | 40.65 | -27.73 | -2.77 | -0.23 | 0.88 | -0.23 | 3.92 | -0.37 | -0.86 | 23.77 | 9 |
| 2020 | V2TrendPullback | 70 | 29/41 | 41.43 | 52.97 | 5.30 | 0.76 | 1.58 | 0.76 | 2.66 | 0.70 | 1.92 | 21.14 | 11 |
| 2020 | V2CompressionBreakout | 22 | 5/17 | 22.73 | 1.76 | 0.18 | 0.08 | 1.08 | 0.08 | 0.93 | 0.03 | 0.11 | 11.45 | 8 |
| 2020 | V2RegimeAdaptive | 18 | 10/8 | 55.56 | -0.33 | -0.03 | -0.02 | 0.98 | -0.02 | 0.83 | -0.01 | -0.02 | 8.11 | 2 |
| 2020 | LabBaseline | 210 | 80/130 | 38.10 | 60.83 | 6.08 | 0.29 | 1.22 | 0.29 | 5.28 | 0.92 | 1.93 | 30.38 | 11 |
| 2020 | AlphaBreakout | 143 | 74/69 | 51.75 | 139.47 | 13.95 | 0.97 | 1.84 | 0.98 | 1.88 | 1.99 | 4.60 | 23.78 | 7 |
| 2021 | V2TrendPullback | 71 | 25/46 | 35.21 | -4.94 | -0.49 | -0.07 | 0.95 | -0.07 | 2.60 | -0.07 | -0.17 | 16.32 | 6 |
| 2021 | V2CompressionBreakout | 23 | 8/15 | 34.78 | 9.54 | 0.95 | 0.42 | 1.50 | 0.41 | 0.99 | 0.18 | 0.70 | 11.74 | 7 |
| 2021 | V2RegimeAdaptive | 17 | 8/9 | 47.06 | -8.38 | -0.84 | -0.49 | 0.59 | -0.49 | 0.96 | -0.22 | -0.47 | 6.76 | 2 |
| 2021 | LabBaseline | 203 | 79/124 | 38.92 | -48.37 | -4.84 | -0.24 | 0.87 | -0.24 | 9.73 | -0.64 | -1.43 | 24.33 | 20 |
| 2021 | AlphaBreakout | 124 | 67/57 | 54.03 | 135.06 | 13.51 | 1.09 | 1.96 | 1.09 | 1.83 | 1.91 | 4.30 | 22.69 | 8 |
| 2022 | V2TrendPullback | 44 | 10/34 | 22.73 | -19.66 | -1.97 | -0.45 | 0.72 | -0.45 | 3.23 | -0.32 | -1.10 | 17.20 | 8 |
| 2022 | V2CompressionBreakout | 14 | 3/11 | 21.43 | -1.85 | -0.19 | -0.13 | 0.89 | -0.13 | 0.86 | -0.03 | -0.12 | 11.21 | 4 |
| 2022 | V2RegimeAdaptive | 29 | 16/13 | 55.17 | 4.44 | 0.44 | 0.15 | 1.29 | 0.15 | 0.74 | 0.16 | 0.30 | 7.86 | 5 |
| 2022 | LabBaseline | 213 | 64/149 | 30.05 | -98.39 | -9.84 | -0.46 | 0.71 | -0.46 | 10.88 | -1.57 | -2.88 | 24.68 | 24 |
| 2022 | AlphaBreakout | 95 | 44/51 | 46.32 | 40.22 | 4.02 | 0.42 | 1.34 | 0.42 | 2.17 | 0.62 | 1.44 | 24.92 | 7 |

## Aggregate 2019–2022

| Strategy | Trades | Net USDT | PF | Expectancy | Positive years | Max annual DD % | Top 5 / gross gains % | Top 10 / gross gains % | Largest positive year % |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| V2TrendPullback | 228 | 32.68 | 1.10 | 0.14 | 2/4 | 3.23 | 8.29 | 16.59 | 92.48 |
| V2CompressionBreakout | 77 | 0.69 | 1.01 | 0.01 | 2/4 | 1.83 | 37.57 | 75.10 | 84.41 |
| V2RegimeAdaptive | 84 | -10.18 | 0.85 | -0.12 | 1/4 | 0.96 | 29.09 | 48.76 | 100.00 |
| LabBaseline | 849 | -121.09 | 0.91 | -0.14 | 1/4 | 10.88 | 2.16 | 4.32 | 100.00 |
| AlphaBreakout | 485 | 287.02 | 1.44 | 0.59 | 3/4 | 3.92 | 2.67 | 5.35 | 44.31 |

## Fee sensitivity

| Strategy | Fee / side | Trades | Net USDT | PF | Positive years |
| --- | ---: | ---: | ---: | ---: | ---: |
| V2TrendPullback | 0.100% | 228 | 32.68 | 1.10 | 2/4 |
| V2CompressionBreakout | 0.100% | 77 | 0.69 | 1.01 | 2/4 |
| V2RegimeAdaptive | 0.100% | 84 | -10.18 | 0.85 | 1/4 |
| V2TrendPullback | 0.150% | 228 | 15.69 | 1.05 | 2/4 |
| V2CompressionBreakout | 0.150% | 77 | -5.74 | 0.93 | 1/4 |
| V2RegimeAdaptive | 0.150% | 84 | -18.58 | 0.73 | 1/4 |
| V2TrendPullback | 0.200% | 228 | -4.44 | 0.99 | 1/4 |
| V2CompressionBreakout | 0.200% | 77 | -12.17 | 0.87 | 1/4 |
| V2RegimeAdaptive | 0.200% | 84 | -26.97 | 0.64 | 0/4 |

## Nearby-parameter robustness

| Architecture | Variant | Parameter | Value | Trades | Net USDT | PF | Positive years | Max DD % |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| V2TrendPullback | V2TrendPullbackLo | trend_slope_min | 0.002 | 230 | 29.11 | 1.09 | 2/4 | 3.23 |
| V2TrendPullback | V2TrendPullback | trend_slope_min | 0.003 | 228 | 32.68 | 1.10 | 2/4 | 3.23 |
| V2TrendPullback | V2TrendPullbackHi | trend_slope_min | 0.004 | 221 | 29.61 | 1.09 | 1/4 | 3.21 |
| V2CompressionBreakout | V2CompressionBreakoutLo | compression_ratio_max | 0.75 | 69 | 6.63 | 1.09 | 3/4 | 1.83 |
| V2CompressionBreakout | V2CompressionBreakout | compression_ratio_max | 0.8 | 77 | 0.69 | 1.01 | 2/4 | 1.83 |
| V2CompressionBreakout | V2CompressionBreakoutHi | compression_ratio_max | 0.85 | 86 | 1.40 | 1.02 | 2/4 | 1.83 |
| V2RegimeAdaptive | V2RegimeAdaptiveLo | range_stretch_atr | 1.2 | 84 | -10.18 | 0.85 | 1/4 | 0.96 |
| V2RegimeAdaptive | V2RegimeAdaptive | range_stretch_atr | 1.35 | 84 | -10.18 | 0.85 | 1/4 | 0.96 |
| V2RegimeAdaptive | V2RegimeAdaptiveHi | range_stretch_atr | 1.5 | 84 | -10.18 | 0.85 | 1/4 | 0.96 |

## BTC versus ETH aggregate

| Strategy | Pair | Trades | Net USDT | PF |
| --- | --- | ---: | ---: | ---: |
| V2TrendPullback | BTC/USDT | 113 | 17.47 | 1.12 |
| V2TrendPullback | ETH/USDT | 115 | 15.21 | 1.08 |
| V2CompressionBreakout | BTC/USDT | 46 | -1.05 | 0.98 |
| V2CompressionBreakout | ETH/USDT | 31 | 1.74 | 1.06 |
| V2RegimeAdaptive | BTC/USDT | 47 | -16.97 | 0.52 |
| V2RegimeAdaptive | ETH/USDT | 37 | 6.79 | 1.22 |
| LabBaseline | BTC/USDT | 420 | -52.18 | 0.91 |
| LabBaseline | ETH/USDT | 429 | -68.91 | 0.90 |
| AlphaBreakout | BTC/USDT | 234 | 109.05 | 1.37 |
| AlphaBreakout | ETH/USDT | 251 | 177.97 | 1.51 |

## Classification

- **V2TrendPullback: C — Reject**. Failed criteria: aggregate_pf_gt_1_15, yearly_consistency, year_concentration_le_60pct, nearby_values_stable.
- **V2CompressionBreakout: C — Reject**. Failed criteria: aggregate_pf_gt_1_15, yearly_consistency, year_concentration_le_60pct, sufficient_trades, not_top5_dominated.
- **V2RegimeAdaptive: C — Reject**. Failed criteria: aggregate_pf_gt_1_15, positive_expectancy, yearly_consistency, year_concentration_le_60pct, both_pairs_not_materially_negative, nearby_values_stable, sufficient_trades.

## Audit notes

- Strategy definitions, parameters, fee matrix, references, data hashes, and continuation criteria were frozen before results.
- Prefix consistency, future mutation, prior-extrema, exclusive regime ownership, timestamp ordering, duplicates, gaps, source-pattern, and hash checks passed.
- Freqtrade executes signals on the following candle. Rolling extrema are shifted one candle and no centered/future windows or future fills exist.
- Detailed pair-year, exit-reason, setup/regime contribution, concentration, parameter, and fee tables are retained as machine-readable CSV files.

# Phase 4B locked retrospective robustness evaluation

**Every result below is retrospective robustness evidence only. None is a new or untouched holdout.**

**Classification: C. Fails robustness testing.**

AlphaBreakout was frozen before retrieval or evaluation. No parameter, feature, exit, fee, model or period was changed after the manifest.

## Frozen configuration

- AlphaBreakout: 24h prior-high breakout + 0.1 ATR14; NATR above prior24h mean; relative volume >=1.2; close location >=0.75; positive volume.
- Exit: close below prior12h low; ROI 5%; stoploss -5%; no trailing.
- 1h Binance spot BTC/USDT and ETH/USDT; 0.1% fee per side; 100 USDT stake; 1,000 USDT wallet; max two positions; next-candle limit execution.
- Frozen UTC: 2026-09-22T01:17:01.451573+00:00; Git commit: c1d41e8175b124d93cdc7e224f2b07badb8fd9da; manifest SHA256: c5d62de8edbccaf03053505d45eeef8a3c532793796a27bb83633dcd1de2e846

## Period portfolio results

| Period | Strategy | Trades | Win / loss | Win % | Net USDT | Return % | Avg trade % | PF | Expectancy | Wallet DD % | Sharpe | Sortino | Duration h | Loss streak |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| A_2023 | AlphaBreakout | 131 | 53 / 78 | 40.46 | -2.59 | -0.26 | -0.02 | 0.98 | -0.02 | 4.69 | -0.04 | -0.10 | 26.56 | 16 |
| A_2023 | LabBaseline | 217 | 72 / 145 | 33.18 | -5.92 | -0.59 | -0.03 | 0.97 | -0.03 | 6.04 | -0.12 | -0.24 | 31.75 | 15 |
| B_2024 | AlphaBreakout | 127 | 62 / 65 | 48.82 | 74.20 | 7.42 | 0.59 | 1.59 | 0.58 | 1.99 | 1.23 | 2.51 | 26.01 | 6 |
| B_2024 | LabBaseline | 205 | 73 / 132 | 35.61 | -43.35 | -4.34 | -0.21 | 0.84 | -0.21 | 9.49 | -0.74 | -1.50 | 30.91 | 16 |
| C_2025_to_2026Q1 | AlphaBreakout | 161 | 58 / 103 | 36.02 | -30.69 | -3.07 | -0.19 | 0.84 | -0.19 | 4.61 | -0.46 | -1.00 | 23.71 | 9 |
| C_2025_to_2026Q1 | LabBaseline | 253 | 81 / 172 | 32.02 | -96.06 | -9.61 | -0.38 | 0.75 | -0.38 | 12.05 | -1.26 | -2.35 | 31.96 | 12 |
| D_2026_shadow | AlphaBreakout | 60 | 21 / 39 | 35.00 | -16.89 | -1.69 | -0.28 | 0.77 | -0.28 | 3.50 | -0.77 | -1.72 | 25.42 | 10 |
| D_2026_shadow | LabBaseline | 78 | 30 / 48 | 38.46 | 1.30 | 0.13 | 0.02 | 1.02 | 0.02 | 2.34 | 0.06 | 0.14 | 43.50 | 7 |

## Aggregate across four separately reset retrospective runs

| Strategy | Trades | Net USDT | Sum returns % | PF | Expectancy | Profitable periods | PF>1 periods | Worst period | Max wallet DD |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| AlphaBreakout | 479 | 24.02 | 2.40 | 1.04 | 0.05 | 1/4 | 1/4 | -30.69 | 4.69 |
| LabBaseline | 753 | -144.03 | -14.40 | 0.85 | -0.19 | 1/4 | 1/4 | -96.06 | 12.05 |

Period returns are summed, not compounded, because each run starts with a fresh 1,000 USDT wallet.

## BTC / ETH results

| Period | Strategy | Pair | Trades | Net USDT | PF | Win % |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| A_2023 | AlphaBreakout | BTC/USDT | 63 | 8.96 | 1.12 | 38.10 |
| A_2023 | AlphaBreakout | ETH/USDT | 68 | -11.55 | 0.87 | 42.65 |
| A_2023 | LabBaseline | BTC/USDT | 115 | -17.64 | 0.83 | 32.17 |
| A_2023 | LabBaseline | ETH/USDT | 102 | 11.72 | 1.11 | 34.31 |
| B_2024 | AlphaBreakout | BTC/USDT | 63 | 47.92 | 1.88 | 53.97 |
| B_2024 | AlphaBreakout | ETH/USDT | 64 | 26.28 | 1.36 | 43.75 |
| B_2024 | LabBaseline | BTC/USDT | 106 | -2.19 | 0.98 | 41.51 |
| B_2024 | LabBaseline | ETH/USDT | 99 | -41.16 | 0.72 | 29.29 |
| C_2025_to_2026Q1 | AlphaBreakout | BTC/USDT | 79 | -19.83 | 0.74 | 35.44 |
| C_2025_to_2026Q1 | AlphaBreakout | ETH/USDT | 82 | -10.86 | 0.91 | 36.59 |
| C_2025_to_2026Q1 | LabBaseline | BTC/USDT | 125 | -59.08 | 0.61 | 28.00 |
| C_2025_to_2026Q1 | LabBaseline | ETH/USDT | 128 | -36.99 | 0.84 | 35.94 |
| D_2026_shadow | AlphaBreakout | BTC/USDT | 32 | -0.15 | 0.99 | 37.50 |
| D_2026_shadow | AlphaBreakout | ETH/USDT | 28 | -16.74 | 0.64 | 32.14 |
| D_2026_shadow | LabBaseline | BTC/USDT | 36 | -0.09 | 1.00 | 41.67 |
| D_2026_shadow | LabBaseline | ETH/USDT | 42 | 1.39 | 1.03 | 35.71 |

## Exit-reason contribution: AlphaBreakout

| Period | Exit | Trades | Net USDT |
| --- | ---: | ---: | ---: |
| A_2023 | breakout_exit | 101 | -122.02 |
| A_2023 | roi | 27 | 134.99 |
| A_2023 | stop_loss | 3 | -15.56 |
| B_2024 | breakout_exit | 86 | -63.18 |
| B_2024 | force_exit | 1 | -1.26 |
| B_2024 | roi | 34 | 169.76 |
| B_2024 | stop_loss | 6 | -31.13 |
| C_2025_to_2026Q1 | breakout_exit | 130 | -144.81 |
| C_2025_to_2026Q1 | roi | 27 | 134.85 |
| C_2025_to_2026Q1 | stop_loss | 4 | -20.73 |
| D_2026_shadow | breakout_exit | 49 | -61.64 |
| D_2026_shadow | roi | 10 | 49.94 |
| D_2026_shadow | stop_loss | 1 | -5.19 |

## Robustness interpretation

- AlphaBreakout is profitable in 1 of 4 periods with aggregate net 24.02 USDT and PF 1.04.
- LabBaseline aggregate net is -144.03 USDT and PF 0.85 over the same periods.
- Evaluate recent periods C and D directly: deterioration there prevents treating older gains as proof of continuing performance.
- Pair tables identify whether one asset accounts for the result; concentration and small trade counts are retained as limitations, not filtered away.
- Drawdown is engine wallet drawdown for full portfolios. Max consecutive losses use close-time order, with pair as tie-breaker.
- Different periods contain different market regimes, but this evaluation does not use results to define or select regimes.
- There is no prospective paper-trading evidence. Category A is therefore not available from this phase.

## Audit results

- Frozen source, copied strategy and LabBaseline hashes matched before and after runs.
- Causality tests passed: prefix consistency, future-price mutation, prior-high leakage check, real timestamp ordering, duplicate checks and next-candle signal validation.
- Both pairs contain a single confirmed Binance 2023-03-24 13:00 UTC gap before period D. It is explicitly synthetic (prior close OHLC, zero volume); period D source is exact sealed data with no missing/duplicate candles.
- No data beyond 2026-09-01, no ML/FreqAI, no parameter variants, and no modifications to the original seal occurred.
- Backtest output may force-close positions at an end boundary. Such trades are retained, not discarded.
- An execution-session recovery caused C to run twice under the same locked command. Both archives are preserved; their full metadata differs, while their strategy-level economic summaries are identical. No alternate setting was evaluated.

Full period, pair, aggregate, exit and source-hash files are retained in reports/ and audits/.

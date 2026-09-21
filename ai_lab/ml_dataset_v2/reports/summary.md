# Phase 3B review

**Six years: 2019-01-01 through 2025-01-01 exclusive, UTC.**
Dec 2018 is warmup only. No 2025/2026 prices are used. 2023 and 2024 are already-observed development history.

Dataset A: 1271 actual portfolio trades. Dataset B: 1271 independent signal opportunities.
Final predictors: 42 numeric + pair/regime = 44 total.
All 1,271 valid signals reconcile to independent trades. All shared outcomes match the portfolio run.

## Candles per pair/year

| Pair | Year | Grid hours | Observed | Explicit filled gaps | Raw zero-volume |
| --- | ---: | ---: | ---: | ---: | ---: |
| BTCUSDT | 2019 | 8760 | 8732 | 28 | 1 |
| BTCUSDT | 2020 | 8784 | 8766 | 18 | 0 |
| BTCUSDT | 2021 | 8760 | 8747 | 13 | 1 |
| BTCUSDT | 2022 | 8760 | 8760 | 0 | 0 |
| BTCUSDT | 2023 | 8760 | 8759 | 1 | 1 |
| BTCUSDT | 2024 | 8784 | 8784 | 0 | 0 |
| ETHUSDT | 2019 | 8760 | 8732 | 28 | 1 |
| ETHUSDT | 2020 | 8784 | 8766 | 18 | 0 |
| ETHUSDT | 2021 | 8760 | 8747 | 13 | 1 |
| ETHUSDT | 2022 | 8760 | 8760 | 0 | 0 |
| ETHUSDT | 2023 | 8760 | 8759 | 1 | 1 |
| ETHUSDT | 2024 | 8784 | 8784 | 0 | 0 |

Each pair has 52,608 scored grid hours: 52,548 observed plus 60 explicitly marked gap fills.
All gaps were re-requested from Binance; maximum consecutive gap is 10 hours.
Raw data has three zero-volume candles per pair. Large-change flags: BTC 6, ETH 13.
Flags use >10% close returns or >2% open/previous-close gaps and are retained, not silently corrected.

## Rows, label balance and outcomes by entry year

| Year | A rows | B rows | Winners | Win % | >0.5% | >1% | Stoploss | Net USDT |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2019 | 223 | 223 | 72 | 32.29 | 59 | 57 | 19 | -35.166 |
| 2020 | 210 | 210 | 80 | 38.10 | 74 | 72 | 22 | 63.206 |
| 2021 | 203 | 203 | 79 | 38.92 | 76 | 73 | 43 | -46.372 |
| 2022 | 213 | 213 | 64 | 30.05 | 55 | 52 | 31 | -98.247 |
| 2023 | 217 | 217 | 73 | 33.64 | 58 | 47 | 8 | -0.803 |
| 2024 | 205 | 205 | 73 | 35.61 | 59 | 50 | 15 | -43.445 |

A and B are the same events and must not be concatenated as independent samples.
These are entry-year contributions from one continuous backtest. Trades can cross years;
previous reset-year reports forced positions closed at boundaries, so outcomes can differ.

## Pair differences

| Pair | Rows | Win % | Net USDT | Average trade % |
| --- | ---: | ---: | ---: | ---: |
| BTC/USDT | 641 | 34.63 | -63.819 | -0.100 |
| ETH/USDT | 630 | 34.76 | -97.007 | -0.154 |

## Regime differences

| Entry regime | Rows | Win % | Net USDT | Average trade % |
| --- | ---: | ---: | ---: | ---: |
| HIGH_VOLATILITY | 157 | 35.03 | -124.282 | -0.792 |
| LOW_VOLATILITY | 48 | 14.58 | -10.106 | -0.210 |
| RANGE | 788 | 34.39 | -25.213 | -0.032 |
| TREND_DOWN | 22 | 31.82 | -13.650 | -0.621 |
| TREND_UP | 256 | 39.45 | 12.425 | 0.048 |

HIGH_VOLATILITY accounts for -124.282 USDT across 157 signals; TREND_UP is modestly positive
(+12.425 USDT across 256). These pooled descriptive differences are not filter recommendations.
2021 has the highest stoploss rate (21.18%); 2022 has the weakest net result (-98.247 USDT).
2020 is the only positive entry-year contribution (+63.206 USDT).

## Distribution drift

| Pair | Year | Feature | KS vs pair 2019 | Standardized mean shift |
| --- | ---: | --- | ---: | ---: |
| ETH/USDT | 2023 | return_std_168 | 0.549 | -1.047 |
| BTC/USDT | 2021 | return_std_24 | 0.529 | 0.813 |
| ETH/USDT | 2023 | natr14 | 0.521 | -1.093 |
| ETH/USDT | 2021 | return_std_24 | 0.482 | 1.173 |
| ETH/USDT | 2021 | distance_low_24 | 0.477 | 1.157 |
| BTC/USDT | 2021 | natr14 | 0.472 | 1.039 |
| ETH/USDT | 2021 | natr14 | 0.438 | 1.440 |
| BTC/USDT | 2021 | return_std_168 | 0.430 | 0.762 |
| ETH/USDT | 2023 | return_std_24 | 0.429 | -0.788 |
| BTC/USDT | 2023 | natr14 | 0.407 | -0.801 |

Volatility distributions shift substantially across years: ETH 2023 weekly volatility is lower
than its 2019 reference, while BTC/ETH 2021 volatility is higher. KS and standardized shifts
are descriptive; correlated trade observations invalidate naive IID significance claims.
Complete pair-by-year distributions and pair-specific KS comparisons are included in CSV reports.

## Chronological overlap controls

| Internal evaluation year | Training rows | Evaluation rows | Train purged/embargoed | Test right-edge exclusions |
| --- | ---: | ---: | ---: | ---: |
| 2020 | 221 | 208 | 2 | 2 |
| 2021 | 431 | 201 | 2 | 2 |
| 2022 | 634 | 210 | 2 | 3 |
| 2023 | 845 | 216 | 4 | 1 |
| 2024 | 1065 | 203 | 1 | 2 |

Counts are identical for B. The interval end includes the later of strategy exit and entry+48h.
Training intervals must end before the test-year boundary minus 48 hours. Test labels crossing
the right boundary are excluded. Exact IDs are stored in folds.json. No random shuffling.
794 rows overlap at least one earlier label interval; maximum concurrent label intervals is six.
This dependence survives a larger row count and must be respected in future training/uncertainty.

## Audit results and limitations

- Six synthetic/dataset tests passed; 66 real prefix comparisons per pair and future mutation checks passed.
- No duplicate signal rows, missing predictors, infinities, ordering failures or train/test label overlap.
- Two final opportunities have incomplete forward horizons; labels stay null. One terminal force exit is flagged.
- No feature/outcome Pearson or Spearman correlations reached absolute 0.95.
- The proposed rolling drawdown feature duplicated distance_high_168 (r 0.988–0.998 by year); removed without outcome-based selection.
- Raw ATR, candle body return and MACD histogram were consolidated as documented. Final redundancy screen is retained.
- Current exchange metadata and hourly fill assumptions are not historically exact execution. Synthetic gap candles may affect indicators.

## Sample-size conclusion

Historical expansion raises unique examples from 422 to 1,271: +849, or 3.01x. This is a useful increase
in observed history but remains a modest, dependent dataset across changing market conditions.
Independent opportunities add ZERO unique examples for this baseline. No suppressed signals were found:
the crossover exit generally closes a position before the next upward crossover, and two portfolio slots
cover the two pairs. Dataset B validates this rather than artificially inflating sample size.
No ML was trained, no optimization performed, no strategy changed, and the shadow was never accessed.

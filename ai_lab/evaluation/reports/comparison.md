# Phase 2A comparison

Fixed LabBaseline; no parameter selection or model training.
All periods UTC, end-exclusive. Every run resets to 1,000 USDT; fees 0.1% per side.

## All runs

| Run | Start | End exclusive | Candles/pair | Return % | Trades | Win % | PF | Expectancy USDT | Wallet DD % |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| development | 2023-01-01 | 2024-01-01 | 8760 | -0.598 | 217 | 33.18 | 0.972 | -0.0276 | 6.035 |
| validation | 2024-01-01 | 2025-01-01 | 8784 | -4.344 | 205 | 35.61 | 0.842 | -0.2119 | 9.489 |
| wf1_development | 2023-01-01 | 2023-07-01 | 4344 | 0.515 | 110 | 35.45 | 1.041 | 0.0468 | 3.452 |
| wf1_validation | 2023-07-01 | 2023-10-01 | 2208 | -3.248 | 63 | 19.05 | 0.282 | -0.5155 | 4.334 |
| wf2_development | 2023-04-01 | 2023-10-01 | 4392 | -2.902 | 122 | 26.23 | 0.731 | -0.2379 | 4.994 |
| wf2_validation | 2023-10-01 | 2024-01-01 | 2208 | 1.644 | 44 | 45.45 | 1.391 | 0.3737 | 1.445 |
| wf3_development | 2023-07-01 | 2024-01-01 | 4416 | -1.088 | 107 | 30.84 | 0.875 | -0.1017 | 4.334 |
| wf3_validation | 2024-01-01 | 2024-04-01 | 2184 | 0.930 | 57 | 40.35 | 1.144 | 0.1631 | 3.033 |
| wf4_development | 2023-10-01 | 2024-04-01 | 4392 | 3.092 | 101 | 43.56 | 1.291 | 0.3061 | 2.971 |
| wf4_validation | 2024-04-01 | 2024-07-01 | 2184 | -4.609 | 51 | 23.53 | 0.497 | -0.9037 | 5.769 |
| wf5_development | 2024-01-01 | 2024-07-01 | 4368 | -4.590 | 108 | 30.56 | 0.716 | -0.4250 | 7.722 |
| wf5_validation | 2024-07-01 | 2024-10-01 | 2208 | 0.110 | 48 | 39.58 | 1.019 | 0.0229 | 3.356 |
| wf6_development | 2024-04-01 | 2024-10-01 | 4392 | -4.694 | 99 | 31.31 | 0.689 | -0.4742 | 7.575 |
| wf6_validation | 2024-10-01 | 2025-01-01 | 2208 | 0.331 | 49 | 42.86 | 1.061 | 0.0675 | 2.144 |
| test | 2025-04-01 | 2026-04-01 | 8760 | -3.097 | 199 | 33.67 | 0.884 | -0.1556 | 6.038 |

## Risk and trade detail

| Run | Sharpe | Sortino | Wallet Sharpe | Wallet Sortino | Avg trade % | Avg duration | Consecutive losses | Fees USDT | Market change % |
| --- | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: |
| development | -0.120 | -0.248 | -0.094 | -0.124 | -0.028 | 1 day, 7:45:00 | 15 | 43.3851 | 123.45 |
| validation | -0.742 | -1.505 | -0.741 | -0.979 | -0.212 | 1 day, 6:54:00 | 16 | 40.8951 | 82.86 |
| wf1_development | 0.186 | 0.425 | 0.223 | 0.309 | 0.047 | 1 day, 5:34:00 | 8 | 22.0024 | 73.15 |
| wf1_validation | -5.633 | -8.258 | -4.307 | -5.367 | -0.516 | 1 day, 5:38:00 | 15 | 12.5642 | -12.56 |
| wf2_development | -1.411 | -2.860 | -1.292 | -1.918 | -0.238 | 1 day, 4:33:00 | 15 | 24.3656 | -6.76 |
| wf2_validation | 1.164 | 2.250 | 1.375 | 1.573 | 0.374 | 1 day, 15:22:00 | 6 | 8.8136 | 46.48 |
| wf3_development | -0.512 | -0.965 | -0.486 | -0.608 | -0.102 | 1 day, 9:56:00 | 15 | 21.3830 | 28.38 |
| wf3_validation | 0.630 | 1.151 | 0.887 | 1.254 | 0.163 | 1 day, 3:44:00 | 8 | 11.3958 | 63.31 |
| wf4_development | 1.048 | 1.974 | 1.279 | 1.609 | 0.306 | 1 day, 9:03:00 | 8 | 20.2146 | 140.92 |
| wf4_validation | -3.212 | -6.564 | -3.449 | -3.735 | -0.906 | 1 day, 2:48:00 | 16 | 10.1374 | -8.47 |
| wf5_development | -1.543 | -3.034 | -1.659 | -1.931 | -0.426 | 1 day, 3:37:00 | 16 | 21.5240 | 48.78 |
| wf5_validation | 0.076 | 0.164 | 0.104 | 0.172 | 0.024 | 1 day, 10:35:00 | 8 | 9.5908 | -11.90 |
| wf6_development | -1.607 | -3.371 | -1.611 | -2.133 | -0.475 | 1 day, 7:24:00 | 16 | 19.7263 | -19.61 |
| wf6_validation | 0.239 | 0.510 | 0.304 | 0.426 | 0.068 | 1 day, 8:54:00 | 9 | 9.7822 | 37.37 |
| test | -0.513 | -0.952 | -0.644 | -0.800 | -0.156 | 1 day, 9:19:00 | 10 | 39.6824 | -1.23 |

## Pair and exit contributions

Pair contributions use the initial total wallet as denominator. Sharpe/Sortino above
are Freqtrade closed-trade metrics unless labeled wallet. No annual or fold returns
are averaged as if they were a continuous portfolio.

### development

| Pair | Trades | Return contribution % | Net USDT | Win % |
| --- | ---: | ---: | ---: | ---: |
| ETH/USDT | 102 | 1.172 | 11.7234 | 34.31 |
| BTC/USDT | 115 | -1.770 | -17.7041 | 32.17 |

| Exit reason | Trades | Net USDT | Contribution % |
| --- | ---: | ---: | ---: |
| roi | 36 | 179.9830 | 17.998 |
| force_exit | 1 | -0.1871 | -0.019 |
| stop_loss | 8 | -41.5013 | -4.150 |
| sma_cross_down | 172 | -144.2753 | -14.428 |
| TOTAL | 217 | -5.9807 | -0.598 |

### validation

| Pair | Trades | Return contribution % | Net USDT | Win % |
| --- | ---: | ---: | ---: | ---: |
| BTC/USDT | 106 | -0.228 | -2.2831 | 41.51 |
| ETH/USDT | 99 | -4.116 | -41.1619 | 29.29 |

| Exit reason | Trades | Net USDT | Contribution % |
| --- | ---: | ---: | ---: |
| roi | 41 | 204.6788 | 20.468 |
| force_exit | 1 | -0.8689 | -0.087 |
| stop_loss | 15 | -77.7763 | -7.778 |
| sma_cross_down | 148 | -169.4786 | -16.948 |
| TOTAL | 205 | -43.4449 | -4.344 |

### wf1_development

| Pair | Trades | Return contribution % | Net USDT | Win % |
| --- | ---: | ---: | ---: | ---: |
| ETH/USDT | 55 | 1.186 | 11.8586 | 38.18 |
| BTC/USDT | 55 | -0.671 | -6.7060 | 32.73 |

| Exit reason | Trades | Net USDT | Contribution % |
| --- | ---: | ---: | ---: |
| roi | 24 | 119.9925 | 11.999 |
| force_exit | 1 | -0.5522 | -0.055 |
| stop_loss | 4 | -20.7560 | -2.076 |
| sma_cross_down | 81 | -93.5317 | -9.353 |
| TOTAL | 110 | 5.1526 | 0.515 |

### wf1_validation

| Pair | Trades | Return contribution % | Net USDT | Win % |
| --- | ---: | ---: | ---: | ---: |
| ETH/USDT | 26 | -1.051 | -10.5132 | 19.23 |
| BTC/USDT | 37 | -2.196 | -21.9644 | 18.92 |

| Exit reason | Trades | Net USDT | Contribution % |
| --- | ---: | ---: | ---: |
| roi | 1 | 5.0024 | 0.500 |
| force_exit | 1 | -0.1592 | -0.016 |
| stop_loss | 1 | -5.1885 | -0.519 |
| sma_cross_down | 60 | -32.1324 | -3.213 |
| TOTAL | 63 | -32.4777 | -3.248 |

### wf2_development

| Pair | Trades | Return contribution % | Net USDT | Win % |
| --- | ---: | ---: | ---: | ---: |
| ETH/USDT | 55 | 0.102 | 1.0216 | 30.91 |
| BTC/USDT | 67 | -3.004 | -30.0430 | 22.39 |

| Exit reason | Trades | Net USDT | Contribution % |
| --- | ---: | ---: | ---: |
| roi | 13 | 65.0033 | 6.500 |
| force_exit | 1 | -0.1592 | -0.016 |
| stop_loss | 2 | -10.3755 | -1.038 |
| sma_cross_down | 106 | -83.4900 | -8.349 |
| TOTAL | 122 | -29.0214 | -2.902 |

### wf2_validation

| Pair | Trades | Return contribution % | Net USDT | Win % |
| --- | ---: | ---: | ---: | ---: |
| ETH/USDT | 21 | 1.038 | 10.3780 | 42.86 |
| BTC/USDT | 23 | 0.606 | 6.0635 | 47.83 |

| Exit reason | Trades | Net USDT | Contribution % |
| --- | ---: | ---: | ---: |
| roi | 10 | 49.9882 | 4.999 |
| force_exit | 1 | -0.1871 | -0.019 |
| stop_loss | 3 | -15.5568 | -1.556 |
| sma_cross_down | 30 | -17.8028 | -1.780 |
| TOTAL | 44 | 16.4415 | 1.644 |

### wf3_development

| Pair | Trades | Return contribution % | Net USDT | Win % |
| --- | ---: | ---: | ---: | ---: |
| ETH/USDT | 47 | -0.014 | -0.1352 | 29.79 |
| BTC/USDT | 60 | -1.074 | -10.7419 | 31.67 |

| Exit reason | Trades | Net USDT | Contribution % |
| --- | ---: | ---: | ---: |
| roi | 12 | 59.9905 | 5.999 |
| force_exit | 1 | -0.1871 | -0.019 |
| stop_loss | 4 | -20.7453 | -2.075 |
| sma_cross_down | 90 | -49.9352 | -4.994 |
| TOTAL | 107 | -10.8771 | -1.088 |

### wf3_validation

| Pair | Trades | Return contribution % | Net USDT | Win % |
| --- | ---: | ---: | ---: | ---: |
| BTC/USDT | 30 | 1.394 | 13.9436 | 50.00 |
| ETH/USDT | 27 | -0.464 | -4.6444 | 29.63 |

| Exit reason | Trades | Net USDT | Contribution % |
| --- | ---: | ---: | ---: |
| roi | 13 | 64.9249 | 6.492 |
| force_exit | 2 | 3.5989 | 0.360 |
| stop_loss | 5 | -25.9237 | -2.592 |
| sma_cross_down | 37 | -33.3009 | -3.330 |
| TOTAL | 57 | 9.2992 | 0.930 |

### wf4_development

| Pair | Trades | Return contribution % | Net USDT | Win % |
| --- | ---: | ---: | ---: | ---: |
| BTC/USDT | 53 | 2.518 | 25.1850 | 50.94 |
| ETH/USDT | 48 | 0.573 | 5.7336 | 35.42 |

| Exit reason | Trades | Net USDT | Contribution % |
| --- | ---: | ---: | ---: |
| roi | 24 | 119.9039 | 11.990 |
| force_exit | 2 | 3.5989 | 0.360 |
| stop_loss | 8 | -41.4805 | -4.148 |
| sma_cross_down | 67 | -51.1037 | -5.110 |
| TOTAL | 101 | 30.9186 | 3.092 |

### wf4_validation

| Pair | Trades | Return contribution % | Net USDT | Win % |
| --- | ---: | ---: | ---: | ---: |
| ETH/USDT | 24 | -1.842 | -18.4189 | 20.83 |
| BTC/USDT | 27 | -2.767 | -27.6698 | 25.93 |

| Exit reason | Trades | Net USDT | Contribution % |
| --- | ---: | ---: | ---: |
| roi | 8 | 39.9562 | 3.996 |
| force_exit | 2 | 3.2773 | 0.328 |
| stop_loss | 5 | -25.9140 | -2.591 |
| sma_cross_down | 36 | -63.4083 | -6.341 |
| TOTAL | 51 | -46.0887 | -4.609 |

### wf5_development

| Pair | Trades | Return contribution % | Net USDT | Win % |
| --- | ---: | ---: | ---: | ---: |
| BTC/USDT | 57 | -1.760 | -17.6030 | 36.84 |
| ETH/USDT | 51 | -2.830 | -28.2964 | 23.53 |

| Exit reason | Trades | Net USDT | Contribution % |
| --- | ---: | ---: | ---: |
| roi | 21 | 104.8811 | 10.488 |
| force_exit | 2 | 3.2773 | 0.328 |
| stop_loss | 10 | -51.8377 | -5.184 |
| sma_cross_down | 75 | -102.2202 | -10.222 |
| TOTAL | 108 | -45.8994 | -4.590 |

### wf5_validation

| Pair | Trades | Return contribution % | Net USDT | Win % |
| --- | ---: | ---: | ---: | ---: |
| BTC/USDT | 25 | 0.372 | 3.7156 | 44.00 |
| ETH/USDT | 23 | -0.262 | -2.6174 | 34.78 |

| Exit reason | Trades | Net USDT | Contribution % |
| --- | ---: | ---: | ---: |
| roi | 10 | 49.9138 | 4.991 |
| stop_loss | 3 | -15.5673 | -1.557 |
| sma_cross_down | 35 | -33.2483 | -3.325 |
| TOTAL | 48 | 1.0983 | 0.110 |

### wf6_development

| Pair | Trades | Return contribution % | Net USDT | Win % |
| --- | ---: | ---: | ---: | ---: |
| ETH/USDT | 47 | -2.139 | -21.3918 | 27.66 |
| BTC/USDT | 52 | -2.555 | -25.5502 | 34.62 |

| Exit reason | Trades | Net USDT | Contribution % |
| --- | ---: | ---: | ---: |
| roi | 18 | 89.8701 | 8.987 |
| stop_loss | 8 | -41.4813 | -4.148 |
| sma_cross_down | 73 | -95.3308 | -9.533 |
| TOTAL | 99 | -46.9419 | -4.694 |

### wf6_validation

| Pair | Trades | Return contribution % | Net USDT | Win % |
| --- | ---: | ---: | ---: | ---: |
| BTC/USDT | 24 | 1.320 | 13.2003 | 50.00 |
| ETH/USDT | 25 | -0.989 | -9.8926 | 36.00 |

| Exit reason | Trades | Net USDT | Contribution % |
| --- | ---: | ---: | ---: |
| roi | 10 | 49.8839 | 4.988 |
| force_exit | 1 | -0.8689 | -0.087 |
| stop_loss | 2 | -10.3714 | -1.037 |
| sma_cross_down | 36 | -35.3359 | -3.534 |
| TOTAL | 49 | 3.3077 | 0.331 |

### test

| Pair | Trades | Return contribution % | Net USDT | Win % |
| --- | ---: | ---: | ---: | ---: |
| ETH/USDT | 99 | -0.233 | -2.3307 | 39.39 |
| BTC/USDT | 100 | -2.864 | -28.6396 | 28.00 |

| Exit reason | Trades | Net USDT | Contribution % |
| --- | ---: | ---: | ---: |
| roi | 41 | 204.7439 | 20.474 |
| force_exit | 2 | 2.3973 | 0.240 |
| stop_loss | 22 | -114.0480 | -11.405 |
| sma_cross_down | 134 | -124.0635 | -12.406 |
| TOTAL | 199 | -30.9703 | -3.097 |

## Interpretation and limitations

Positive primary periods: 0/3. Positive walk-forward validation periods: 4/6.
Signs vary across periods if positive and negative windows both occur; this is descriptive
regime dependence, not statistical proof of a regime model or stable future profitability.
The frozen Jan–Mar 2025 reference remains -6.57%, 54 trades, 25.9% wins, PF 0.41, wallet DD 8.52%.

One verified missing hour per pair (2023-03-24 13:00 UTC) is explicitly allowlisted.
Binance's public API confirmed the gap; see gap-verification.json. Freqtrade fills it
with previous-close OHLC and zero volume. Thus 2023 has 8,759 observed candles plus
one synthetic hour per pair. The first walk-forward development window likewise
has one missing source hour. All other windows must have complete raw coverage.
The inserted hour can affect rolling indicators even though volume-gated signals
cannot fire on that candle. No claim of pristine raw data is made.

Range, branch, strategy-hash, config-hash and environment guards were checked.
Causal prefix checks and Freqtrade lookahead results are in results/. These checks
do not establish absence of every possible bias. No positions cross scored windows;
end-of-window force exits affect comparisons. Hourly OHLCV simulation omits realistic
queueing and latency and uses current market metadata. Validation windows overlap
the primary validation data; these are not independent confirmations.

The final test was downloaded/run last after protocol and strategy locking and
non-test checks. It is now consumed. Do not use these test results for optimization
or call them unseen again. Future AI requires a new untouched holdout.

Holdout provenance: a few April 2025 raw candles had been cached outside the earlier
baseline scoring interval. Unseen means not previously evaluated or used for
parameter selection; it does not mean every raw price was never downloaded.

# Phase 5B deterministic alpha failure diagnosis

This is descriptive analysis of previously used 2019–2022 development evidence. It is not a new holdout, does not rerun entry logic, and does not define or recommend filters.

## Overall diagnosis

**Mixed failure led by regime/nonstationarity and exit capture**

1. Regime and volatility dependence: no architecture is broadly stable across contexts.
2. Exit/holding mismatch: favorable excursions are commonly surrendered before close.
3. Entry timing and adverse selection: newer V2 entries have weak early forward returns and frequent immediate adverse movement.
4. Fee fragility: marginal V2 economics disappear between 0.15% and 0.20% per side.
5. Structural nonstationarity: yearly expectancy and entry quality vary materially, especially for AlphaBreakout and V2TrendPullback.
6. Duration dependence: profits frequently sit in longer-duration minorities while short trades lose.
7. Asset dependence: most pronounced in V2RegimeAdaptive; weaker in Trend Pullback and AlphaBreakout.
8. Signal rarity/top-trade dependence: decisive for Compression Breakout and limits Adaptive inference.

## Strategy-level diagnosis

### LabBaseline: A — Entry logic fundamentally weak

PF 0.91; symmetric first-passage is near 50/50; 57.8% of trades were profitable intratrade but closed negative; only >48h trades were strongly profitable.

Ranked causes: poor entry quality, exit giveback, high-volatility dependence, duration dependence.

### AlphaBreakout: E — Structurally unstable / nonstationary

2019 lost while 2020-2021 dominated development gains; high-volatility entries lost and transitional/trend entries dominated. Prior Phase 4B retrospective evidence already established later decay.

Ranked causes: structural nonstationarity, regime dependence, volatility dependence.

### V2TrendPullback: B — Entry useful but exits/risk likely dominate failure

Mean MFE 2.60% versus 0.14% realized; 59.6% profitable intratrade closed negative; 80.5% of structural exits were followed by a +1% continuation; short-duration trades lost heavily.

Ranked causes: exit giveback, regime dependence, duration dependence, fee fragility, entry timing.

### V2CompressionBreakout: D — Too sparse to conclude

Only 77 trades; PF 1.01; 66.2% profitable intratrade closed negative; results turn negative at 0.15% fees and depend on a small set of longer trades.

Ranked causes: signal rarity, duration dependence, fee fragility, exit giveback.

### V2RegimeAdaptive: A — Entry logic fundamentally weak

PF 0.85; 65.5% closed the first hour below entry; BTC PF 0.52 while ETH PF 1.22; transitional entries PF 0.34; only 84 trades.

Ranked causes: adverse selection, asset dependence, regime dependence, signal rarity.

## Entry quality

| Strategy | Trades | MFE % | MAE % | 1h | 3h | 6h | 12h | 24h | 48h |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| LabBaseline | 849 | 2.35 | -2.10 | 0.04 | 0.15 | 0.10 | 0.20 | 0.28 | 0.32 |
| AlphaBreakout | 485 | 2.92 | -1.99 | 0.14 | 0.18 | 0.26 | 0.44 | 0.59 | 1.04 |
| V2TrendPullback | 228 | 2.60 | -1.97 | -0.03 | 0.03 | -0.03 | -0.05 | 0.09 | 0.22 |
| V2CompressionBreakout | 77 | 2.13 | -1.38 | 0.10 | 0.24 | 0.17 | 0.20 | -0.13 | -0.35 |
| V2RegimeAdaptive | 84 | 1.19 | -1.44 | -0.09 | 0.05 | 0.14 | -0.20 | 0.67 | 0.57 |

## Exit quality

| Strategy | Realized % | MFE % | Giveback % | Profitable intratrade, closed negative | Stop recovery | Structural continuation | Time to MFE / MAE h |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| LabBaseline | -0.14 | 2.35 | 2.29 | 491/849 (57.83%) | 37/115 | 348/514 (67.70%) | 12.65 / 13.53 |
| AlphaBreakout | 0.59 | 2.92 | 2.12 | 241/485 (49.69%) | 14/46 | 181/261 (69.35%) | 12.90 / 9.91 |
| V2TrendPullback | 0.14 | 2.60 | 2.25 | 136/228 (59.65%) | 4/8 | 132/164 (80.49%) | 10.86 / 7.62 |
| V2CompressionBreakout | 0.01 | 2.13 | 1.92 | 51/77 (66.23%) | N/A | 33/65 (50.77%) | 5.43 / 4.52 |
| V2RegimeAdaptive | -0.12 | 1.19 | 1.11 | 27/84 (32.14%) | N/A | 64/83 (77.11%) | 4.10 / 3.39 |

## Adverse selection

| Strategy | First-hour adverse % | First-3h adverse % | Any first-hour adverse | First-hour close negative |
| --- | ---: | ---: | ---: | ---: |
| LabBaseline | -0.50 | -0.88 | 98.82% | 50.29% |
| AlphaBreakout | -0.79 | -1.16 | 97.94% | 51.34% |
| V2TrendPullback | -0.68 | -1.14 | 98.68% | 60.53% |
| V2CompressionBreakout | -0.56 | -0.80 | 97.40% | 51.95% |
| V2RegimeAdaptive | -0.55 | -0.94 | 100.00% | 65.48% |

## Same-trade fee sensitivity

| Strategy | 0.10% | 0.15% | 0.20% | 0.25% |
| --- | ---: | ---: | ---: | ---: |
| LabBaseline | -120.97 | -205.63 | -290.21 | -374.70 |
| AlphaBreakout | 286.74 | 238.02 | 189.35 | 140.73 |
| V2TrendPullback | 32.65 | 9.85 | -12.92 | -35.68 |
| V2CompressionBreakout | 0.69 | -7.00 | -14.68 | -22.36 |
| V2RegimeAdaptive | -10.17 | -18.55 | -26.92 | -35.28 |

## Asset dependence

| Strategy | BTC net / PF | ETH net / PF |
| --- | ---: | ---: |
| LabBaseline | -52.18 / 0.91 | -68.91 / 0.90 |
| AlphaBreakout | 109.05 / 1.37 | 177.97 / 1.51 |
| V2TrendPullback | 17.47 / 1.12 | 15.21 / 1.08 |
| V2CompressionBreakout | -1.05 / 0.98 | 1.74 / 1.06 |
| V2RegimeAdaptive | -16.97 / 0.52 | 6.79 / 1.22 |

## Top-trade dependence

| Strategy | Net | Top 5 | Top 10 | Worst 5 | Worst 10 | Median | Trimmed mean |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| LabBaseline | -121.09 | 25.04 | 50.07 | -25.97 | -51.95 | -0.79 | -0.15 |
| AlphaBreakout | 287.02 | 25.04 | 50.06 | -25.97 | -51.94 | -0.12 | 0.67 |
| V2TrendPullback | 32.68 | 30.03 | 60.06 | -30.96 | -58.37 | -1.22 | 0.14 |
| V2CompressionBreakout | 0.69 | 30.02 | 60.00 | -14.47 | -26.24 | -0.94 | -0.11 |
| V2RegimeAdaptive | -10.18 | 16.24 | 27.22 | -16.83 | -31.60 | 0.23 | -0.13 |

## Nonstationarity

| Strategy | 2019 PF / exp | 2020 PF / exp | 2021 PF / exp | 2022 PF / exp |
| --- | ---: | ---: | ---: | ---: |
| LabBaseline | 0.88 / -0.16 | 1.22 / 0.29 | 0.87 / -0.24 | 0.71 / -0.46 |
| AlphaBreakout | 0.88 / -0.23 | 1.84 / 0.98 | 1.96 / 1.09 | 1.34 / 0.42 |
| V2TrendPullback | 1.07 / 0.10 | 1.58 / 0.76 | 0.95 / -0.07 | 0.72 / -0.45 |
| V2CompressionBreakout | 0.58 / -0.49 | 1.08 / 0.08 | 1.50 / 0.41 | 0.89 / -0.13 |
| V2RegimeAdaptive | 0.58 / -0.30 | 0.98 / -0.02 | 0.59 / -0.49 | 1.29 / 0.15 |

## Complete diagnostic tables

Machine-readable tables cover first-passage probabilities, regimes, volatility percentiles, duration, hour, weekday, UTC session, expansion/contraction context, assets, years, exits, fees, adverse selection, and trade concentration. The trade-level Parquet preserves every calculated field.

## Audit conclusion

- Diagnostic definitions were frozen at 2026-09-22T02:30:39.220479+00:00 before outcomes were calculated.
- All source result, candle, and strategy hashes matched the frozen protocol.
- No strategy code was executed or changed, no entry logic was rerun, and no 2023+ candle was loaded.
- All entry context uses the completed signal candle; all future fields are explicitly diagnostic outcomes only.
- Same-trade fee analysis changes costs only and never changes trade selection.
- No result is used to create, promote, or recommend a filter or strategy.

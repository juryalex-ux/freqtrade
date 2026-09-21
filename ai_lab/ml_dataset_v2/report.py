"""Report expanded observed-history datasets without model training."""
import json
from pathlib import Path
import pandas as pd

HERE=Path(__file__).resolve().parent


def main():
    d=pd.read_parquet(HERE/'data/A_portfolio.parquet')
    audit=json.loads((HERE/'audits/dataset-validation.json').read_text())
    candles=pd.read_csv(HERE/'reports/candles-by-year.csv')
    lines=['# Phase 3B review','', '**Six years: 2019-01-01 through 2025-01-01 exclusive, UTC.**',
           'Dec 2018 is warmup only. No 2025/2026 prices are used. 2023 and 2024 are already-observed development history.',
           '', f"Dataset A: {len(d)} actual portfolio trades. Dataset B: {audit['datasets']['B_opportunities']['rows']} independent signal opportunities.",
           f"Final predictors: {audit['numeric_features']} numeric + pair/regime = {audit['feature_count']} total.",
           'All 1,271 valid signals reconcile to independent trades. All shared outcomes match the portfolio run.',
           '', '## Candles per pair/year','', '| Pair | Year | Grid hours | Observed | Explicit filled gaps | Raw zero-volume |',
           '| --- | ---: | ---: | ---: | ---: | ---: |']
    for r in candles.itertuples(): lines.append(f'| {r.pair} | {r.year} | {r.expected} | {r.observed} | {r.synthetic} | {r.observed_zero_volume} |')
    lines+=['','Each pair has 52,608 scored grid hours: 52,548 observed plus 60 explicitly marked gap fills.',
            'All gaps were re-requested from Binance; maximum consecutive gap is 10 hours.',
            'Raw data has three zero-volume candles per pair. Large-change flags: BTC 6, ETH 13.',
            'Flags use >10% close returns or >2% open/previous-close gaps and are retained, not silently corrected.',
            '', '## Rows, label balance and outcomes by entry year','',
            '| Year | A rows | B rows | Winners | Win % | >0.5% | >1% | Stoploss | Net USDT |',
            '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for year,g in d.groupby('year'):
        lines.append(f"| {year} | {len(g)} | {len(g)} | {g.profitable_after_fees.sum()} | {g.profitable_after_fees.mean()*100:.2f} | {g.return_above_0_5_percent.sum()} | {g.return_above_1_percent.sum()} | {g.stoploss_hit.sum()} | {g.net_profit_usdt.sum():.3f} |")
    lines+=['','A and B are the same events and must not be concatenated as independent samples.',
            'These are entry-year contributions from one continuous backtest. Trades can cross years;',
            'previous reset-year reports forced positions closed at boundaries, so outcomes can differ.',
            '', '## Pair differences','', '| Pair | Rows | Win % | Net USDT | Average trade % |', '| --- | ---: | ---: | ---: | ---: |']
    for pair,g in d.groupby('pair'): lines.append(f'| {pair} | {len(g)} | {g.profitable_after_fees.mean()*100:.2f} | {g.net_profit_usdt.sum():.3f} | {g.net_profit_ratio.mean()*100:.3f} |')
    lines+=['','## Regime differences','', '| Entry regime | Rows | Win % | Net USDT | Average trade % |','| --- | ---: | ---: | ---: | ---: |']
    for regime,g in d.groupby('regime'): lines.append(f'| {regime} | {len(g)} | {g.profitable_after_fees.mean()*100:.2f} | {g.net_profit_usdt.sum():.3f} | {g.net_profit_ratio.mean()*100:.3f} |')
    lines+=['','HIGH_VOLATILITY accounts for -124.282 USDT across 157 signals; TREND_UP is modestly positive',
            '(+12.425 USDT across 256). These pooled descriptive differences are not filter recommendations.',
            '2021 has the highest stoploss rate (21.18%); 2022 has the weakest net result (-98.247 USDT).',
            '2020 is the only positive entry-year contribution (+63.206 USDT).',
            '', '## Distribution drift','']
    drift=pd.read_csv(HERE/'reports/year-feature-drift.csv')
    drift=drift[(drift.dataset=='A_portfolio')&(drift.year!=2019)].sort_values('ks_statistic',ascending=False).head(10)
    lines+=['| Pair | Year | Feature | KS vs pair 2019 | Standardized mean shift |','| --- | ---: | --- | ---: | ---: |']
    for r in drift.itertuples(): lines.append(f'| {r.pair} | {r.year} | {r.feature} | {r.ks_statistic:.3f} | {r.standardized_mean_shift:.3f} |')
    lines+=['','Volatility distributions shift substantially across years: ETH 2023 weekly volatility is lower',
            'than its 2019 reference, while BTC/ETH 2021 volatility is higher. KS and standardized shifts',
            'are descriptive; correlated trade observations invalidate naive IID significance claims.',
            'Complete pair-by-year distributions and pair-specific KS comparisons are included in CSV reports.',
            '', '## Chronological overlap controls','', '| Internal evaluation year | Training rows | Evaluation rows | Train purged/embargoed | Test right-edge exclusions |',
            '| --- | ---: | ---: | ---: | ---: |']
    for f in json.loads((HERE/'folds.json').read_text()):
        if f['dataset']=='A_portfolio': lines.append(f"| {f['evaluation_year']} | {f['train_rows']} | {f['test_rows']} | {f['purged_train']} | {f['right_boundary_test_exclusions']} |")
    lines+=['','Counts are identical for B. The interval end includes the later of strategy exit and entry+48h.',
            'Training intervals must end before the test-year boundary minus 48 hours. Test labels crossing',
            'the right boundary are excluded. Exact IDs are stored in folds.json. No random shuffling.',
            '794 rows overlap at least one earlier label interval; maximum concurrent label intervals is six.',
            'This dependence survives a larger row count and must be respected in future training/uncertainty.',
            '', '## Audit results and limitations','',
            '- Six synthetic/dataset tests passed; 66 real prefix comparisons per pair and future mutation checks passed.',
            '- No duplicate signal rows, missing predictors, infinities, ordering failures or train/test label overlap.',
            '- Two final opportunities have incomplete forward horizons; labels stay null. One terminal force exit is flagged.',
            '- No feature/outcome Pearson or Spearman correlations reached absolute 0.95.',
            '- The proposed rolling drawdown feature duplicated distance_high_168 (r 0.988–0.998 by year); removed without outcome-based selection.',
            '- Raw ATR, candle body return and MACD histogram were consolidated as documented. Final redundancy screen is retained.',
            '- Current exchange metadata and hourly fill assumptions are not historically exact execution. Synthetic gap candles may affect indicators.',
            '', '## Sample-size conclusion','',
            'Historical expansion raises unique examples from 422 to 1,271: +849, or 3.01x. This is a useful increase',
            'in observed history but remains a modest, dependent dataset across changing market conditions.',
            'Independent opportunities add ZERO unique examples for this baseline. No suppressed signals were found:',
            'the crossover exit generally closes a position before the next upward crossover, and two portfolio slots',
            'cover the two pairs. Dataset B validates this rather than artificially inflating sample size.',
            'No ML was trained, no optimization performed, no strategy changed, and the shadow was never accessed.']
    (HERE/'reports/summary.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    print('\n'.join(lines[:39]))


if __name__=='__main__': main()

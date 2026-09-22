"""Describe all fixed hypotheses, including failures, without choosing new parameters."""
import json
import subprocess
import sys
import numpy as np
import pandas as pd
from common import HERE,ROOT,CENTRAL,VARIANTS,verify_frozen,save,sha,log,now


def summarize(trades,year):
    d=pd.DataFrame(trades)
    grid=pd.date_range(f'{year}-01-01',f'{year+1}-01-01',inclusive='left',freq='D',tz='UTC')
    daily=pd.Series(0.,index=grid); longest=streak=0
    if len(d):
        d['close_date']=pd.to_datetime(d.close_date,utc=True)
        d=d.sort_values(['close_date','pair'])
        assert (pd.to_datetime(d.open_date,utc=True)>=grid[0]).all()
        boundary=pd.Timestamp(f'{year+1}-01-01',tz='UTC')
        assert (d.close_date<=boundary).all()
        assert (pd.to_datetime(d.open_date,utc=True)<boundary).all()
        assert d.loc[d.close_date==boundary,'exit_reason'].eq('force_exit').all()
        profits=d.profit_abs
        # Retain exact engine closing times in trades/equity. Assign a boundary
        # forced close to the run's final day only for daily ratio accounting.
        closing_day=d.close_date.dt.floor('D').clip(upper=grid[-1])
        daily=d.groupby(closing_day).profit_abs.sum().reindex(grid,fill_value=0.)
        curve=np.r_[1000.,1000+d.groupby('close_date').profit_abs.sum().sort_index().cumsum().to_numpy()]
        avg=float(d.profit_ratio.mean()*100); duration=float(d.trade_duration.mean()/60)
        for value in profits:
            streak=streak+1 if value<0 else 0; longest=max(streak,longest)
    else:
        profits=pd.Series(dtype=float); curve=np.array([1000.]); avg=duration=None
    gains=float(profits[profits>0].sum()); losses=float(-profits[profits<0].sum()); peaks=np.maximum.accumulate(curve)
    returns=daily/1000.; std=returns.std(ddof=1); downside=np.sqrt(np.mean(np.minimum(returns,0)**2))
    return {'trades':len(d),'wins':int((profits>0).sum()),'losses':int((profits<0).sum()),
        'win_rate_pct':float((profits>0).mean()*100) if len(d) else None,
        'total_return_pct':float(profits.sum()/10),'net_usdt':float(profits.sum()),'average_trade_pct':avg,
        'profit_factor':gains/losses if losses else None,'gross_profit_usdt':gains,'gross_loss_usdt':losses,
        'expectancy_usdt':float(profits.mean()) if len(d) else None,
        'closed_trade_drawdown_pct':float(((peaks-curve)/peaks).max()*100),
        'sharpe_daily_closed':float(returns.mean()/std*np.sqrt(365)) if std>0 else None,
        'sortino_daily_closed':float(returns.mean()/downside*np.sqrt(365)) if downside>0 else None,
        'average_duration_hours':duration,'consecutive_losses':longest}


def fmt(x,n=2): return 'N/A' if x is None or pd.isna(x) else f'{x:.{n}f}'


def write_records(path,rows):
    # Pandas normalizes optional metrics to JSON null rather than NaN/Infinity.
    pd.DataFrame(rows).to_json(path,orient='records',indent=2)


def main():
    protocol=verify_frozen(); rows=[]; exits=[]; all_trades=[]
    for year in [2019,2020,2021,2022]:
        values=json.loads((HERE/'results'/str(year)/'metrics.json').read_text())
        for name,m in values.items():
            trades=m['trades']; overall=summarize(trades,year)
            assert abs(overall['net_usdt']-m['profit_total_abs'])<1e-6
            assert overall['trades']==m['total_trades']
            wallet=m.get('wallet_stats',{})
            for pair in ['ALL','BTC/USDT','ETH/USDT']:
                part=trades if pair=='ALL' else [t for t in trades if t['pair']==pair]
                metric=overall if pair=='ALL' else summarize(part,year)
                rows.append({'strategy':name,'year':year,'pair':pair,**metric,
                    'wallet_drawdown_pct':float(wallet.get('max_drawdown_account',m['max_drawdown_account'])*100) if pair=='ALL' else None,
                    'engine_sharpe':m.get('sharpe') if pair=='ALL' else None,
                    'engine_sortino':m.get('sortino') if pair=='ALL' else None,
                    'rejected_signals':m.get('rejected_signals') if pair=='ALL' else None})
                for reason in sorted({t['exit_reason'] for t in part}):
                    selected=[t for t in part if t['exit_reason']==reason]
                    exits.append({'strategy':name,'year':year,'pair':pair,'exit_reason':reason,
                        'trades':len(selected),'wins':sum(t['profit_abs']>0 for t in selected),
                        'net_usdt':sum(t['profit_abs'] for t in selected),
                        'return_contribution_pct':sum(t['profit_abs'] for t in selected)/10})
            all_trades.extend({'strategy':name,'year':year,**t} for t in trades)
    yearly=pd.DataFrame(rows); yearly.to_csv(HERE/'reports/yearly-metrics.csv',index=False)
    write_records(HERE/'reports/yearly-metrics.json',rows)
    pd.DataFrame(exits).to_csv(HERE/'reports/exit-contributions.csv',index=False)
    pd.DataFrame(all_trades).to_parquet(HERE/'reports/all-trades.parquet',index=False)
    totals=[]
    for (name,pair),g in yearly.groupby(['strategy','pair']):
        gains=g.gross_profit_usdt.sum(); losses=g.gross_loss_usdt.sum(); count=int(g.trades.sum())
        totals.append({'strategy':name,'pair':pair,'trades':count,'net_usdt':float(g.net_usdt.sum()),
            'mean_annual_return_pct':float(g.total_return_pct.mean()),
            'sum_annual_return_pct':float(g.total_return_pct.sum()),
            'win_rate_pct':float(g.wins.sum()/count*100) if count else None,
            'profit_factor':float(gains/losses) if losses else None,
            'expectancy_usdt':float(g.net_usdt.sum()/count) if count else None,
            'positive_years':int(g.net_usdt.gt(0).sum()),'pf_above_one_years':int(g.profit_factor.gt(1).sum()),
            'worst_year_usdt':float(g.net_usdt.min()),'median_year_usdt':float(g.net_usdt.median()),
            'max_year_wallet_drawdown_pct':float(g.wallet_drawdown_pct.max()) if pair=='ALL' else None,
            'max_year_closed_drawdown_pct':float(g.closed_trade_drawdown_pct.max()),
            'min_year_trades':int(g.trades.min()),
            'largest_positive_year_share':float(g.net_usdt.clip(lower=0).max()/g.net_usdt.clip(lower=0).sum()) if g.net_usdt.gt(0).any() else None})
    total=pd.DataFrame(totals); total.to_csv(HERE/'reports/aggregate-metrics.csv',index=False)
    walk=[]
    for name in ['LabBaseline',*VARIANTS]:
        for year in [2021,2022]:
            prior=yearly[(yearly.strategy==name)&(yearly.pair=='ALL')&(yearly.year<year)]
            test=yearly[(yearly.strategy==name)&(yearly.pair=='ALL')&(yearly.year==year)].iloc[0]
            walk.append({'strategy':name,'past_years':f'2019-{year-1}','evaluation_year':year,
                'past_trades':int(prior.trades.sum()),'past_net_usdt':float(prior.net_usdt.sum()),
                **{k:test[k] for k in ['trades','win_rate_pct','net_usdt','total_return_pct','profit_factor','expectancy_usdt','wallet_drawdown_pct','sharpe_daily_closed','sortino_daily_closed']},
                'fitting_or_parameter_updates':0})
    pd.DataFrame(walk).to_csv(HERE/'reports/walk-forward.csv',index=False)
    decisions=[]; robustness=[]; c=protocol['acceptance']
    for name in CENTRAL:
        base=total[(total.strategy==name)&(total.pair=='ALL')].iloc[0]
        variants=total[(total.strategy.isin([name+'Lo',name+'Hi']))&(total.pair=='ALL')]
        pairs=total[(total.strategy==name)&(total.pair!='ALL')]
        last=yearly[(yearly.strategy==name)&(yearly.pair=='ALL')&(yearly.year==2022)].iloc[0]
        checks={
            'positive_expectancy_multiple_years':int(base.positive_years)>=c['positive_expectancy_years_min'],
            'pf_above_one_multiple_years':int(base.pf_above_one_years)>=c['pf_above_one_years_min'],
            'aggregate_positive':base.net_usdt>0,
            'sufficient_total_trades':base.trades>=c['minimum_total_trades'],
            'sufficient_each_year':base.min_year_trades>=c['minimum_trades_each_year'],
            'wallet_drawdown_acceptable':base.max_year_wallet_drawdown_pct<=c['max_yearly_wallet_drawdown_pct'],
            'not_one_positive_year_dominated':pd.notna(base.largest_positive_year_share) and base.largest_positive_year_share<=c['largest_positive_year_share_max'],
            'both_pairs_positive':bool(pairs.net_usdt.gt(0).all()),
            'internal_2022_positive':last.net_usdt>0,
            'both_neighbors_positive':bool(variants.net_usdt.gt(0).all()),
            'neighbors_multiple_positive_years':bool(variants.positive_years.ge(c['each_perturbation_positive_years_min']).all())}
        checks={k:bool(v) for k,v in checks.items()}
        decisions.append({'strategy':name,'continue':all(checks.values()),'checks':checks,'failed':[k for k,v in checks.items() if not v]})
        values=protocol['candidates'][name]['perturbation']['values']
        for variant,value in zip([name+'Lo',name,name+'Hi'],values):
            a=total[(total.strategy==variant)&(total.pair=='ALL')].iloc[0]
            annual=yearly[(yearly.strategy==variant)&(yearly.pair=='ALL')].sort_values('year')
            robustness.append({'candidate':name,'variant':variant,'parameter':protocol['candidates'][name]['perturbation']['parameter'],
                'value':value,'trades':int(a.trades),'net_usdt':a.net_usdt,'profit_factor':a.profit_factor,
                'positive_years':int(a.positive_years),'worst_year_usdt':a.worst_year_usdt,
                **{f'net_{int(r.year)}':r.net_usdt for r in annual.itertuples()}})
    save(HERE/'reports/decisions.json',decisions)
    pd.DataFrame(robustness).to_csv(HERE/'reports/robustness.csv',index=False)
    core=yearly[(yearly.strategy.isin(['LabBaseline',*CENTRAL]))&(yearly.pair=='ALL')]
    lines=['# Phase 4A deterministic alpha research','',
        'Only 2019-2022 outcomes were evaluated. All five candidate definitions, one-parameter neighborhoods and acceptance criteria were frozen before viewing results.',
        'The preceding December supplies warmup only. No consumed-period dataset or performance file is read by this workflow.',
        '2019-2022 were used in earlier research, so these are development results, not a pristine holdout.',
        '', '## Candidate definitions','']
    for name,desc in protocol['candidates'].items():
        lines += [f'### {name}', '', 'Entry: '+desc['entry']+'.', '', 'Structural exit: '+desc['exit']+'.', '',
                  'Rationale: '+desc['rationale'], '', 'Perturbation: '+str(desc['perturbation']), '']
    lines += ['All candidates also use unchanged baseline-like 5% ROI and -5% stoploss, positive entry volume, first true-condition candle only, and next-candle engine execution. These are isolated strategy classes, not a change to LabBaseline.',
        '', '## Annual portfolio metrics','',
        '| Candidate | Year | Trades | Win % | Return % | Net USDT | Avg trade % | PF | Expectancy | Wallet DD % | Sharpe | Sortino | Duration h | Loss streak |',
        '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for name in ['LabBaseline',*CENTRAL]:
        for r in core[core.strategy==name].sort_values('year').itertuples():
            lines.append(f'| {name} | {r.year} | {r.trades} | {fmt(r.win_rate_pct)} | {fmt(r.total_return_pct)} | {fmt(r.net_usdt)} | {fmt(r.average_trade_pct)} | {fmt(r.profit_factor)} | {fmt(r.expectancy_usdt)} | {fmt(r.wallet_drawdown_pct)} | {fmt(r.sharpe_daily_closed)} | {fmt(r.sortino_daily_closed)} | {fmt(r.average_duration_hours)} | {r.consecutive_losses} |')
    lines += ['','Sharpe/Sortino here use a full calendar of daily closed P/L divided by a fixed 1000 USDT wallet, annualized sqrt365, with zero-risk-free return. Sortino downside RMS includes zero-return days. Undefined ratios are N/A. Engine-native portfolio ratios are retained separately in yearly-metrics.csv.',
        'Wallet DD is the engine wallet-statistics drawdown. Pair closed-trade DD uses the common1000 USDT basis; do not add pair drawdowns. Annual wallets reset; summed returns are not a compounded strategy return.',
        'Engine timeranges include the next January1 midnight endpoint where present: seven forced exits across the2020/2021 strategy runs close exactly on that boundary. Their exact timestamps are retained and P/L assigned to the preceding final calendar day for daily ratios. No post2022 candles exist in the input;2022 ends Dec31 23:00. Thus yearly runs touch at a boundary point rather than being strictly disjoint; no fitting or parameter adaptation occurs across it.',
        '', '## Aggregate and pair comparison','',
        '| Candidate | Pair | Trades | Net USDT | PF | Positive years | Expectancy USDT |','| --- | --- | ---: | ---: | ---: | ---: | ---: |']
    for name in ['LabBaseline',*CENTRAL]:
        for r in total[total.strategy==name].itertuples():
            lines.append(f'| {name} | {r.pair} | {r.trades} | {fmt(r.net_usdt)} | {fmt(r.profit_factor)} | {r.positive_years}/4 | {fmt(r.expectancy_usdt)} |')
    lines += ['', '## Walk-forward evaluation','',
        'No fitting or calibration applies to these deterministic rules. After2019-2020 initial-design context,2021 is the next-year check; after2019-2021 context,2022 is the final internal check. Definitions and central values stay frozen, including after2021.',
        '', '| Candidate | 2021 net | 2021 PF | 2022 net | 2022 PF |','| --- | ---: | ---: | ---: | ---: |']
    for name in ['LabBaseline',*CENTRAL]:
        a=core[(core.strategy==name)&(core.year==2021)].iloc[0]; b=core[(core.strategy==name)&(core.year==2022)].iloc[0]
        lines.append(f'| {name} | {fmt(a.net_usdt)} | {fmt(a.profit_factor)} | {fmt(b.net_usdt)} | {fmt(b.profit_factor)} |')
    lines += ['', '## Nearby-parameter robustness','', '| Candidate | Parameter | Value | Trades | Net USDT | PF | Positive years |','| --- | --- | ---: | ---: | ---: | ---: | ---: |']
    for r in robustness: lines.append(f"| {r['candidate']} | {r['parameter']} | {r['value']} | {r['trades']} | {fmt(r['net_usdt'])} | {fmt(r['profit_factor'])} | {r['positive_years']}/4 |")
    lines += ['', 'Only the original central settings can continue. A neighbor is never promoted because its result is better. Full yearly and pair metrics for every neighbor are retained.',
        '', '## Predeclared decisions','']
    for r in decisions: lines.append(f"- {r['strategy']}: {'eligible to freeze for later evaluation' if r['continue'] else 'reject for continuation'}; failed checks: {', '.join(r['failed']) or 'none'}.")
    lines += ['', 'Acceptance requires three positive-expectancy/PF>1 years; aggregate positive;100 trades total and15 each year; max yearly wallet DD<=10%; no year>65% of total positive yearly P/L; both pairs positive;2022 positive; both neighbors positive overall and at least two positive years each.',
        'These rules support research triage, not deployment. No future or consumed-period evaluation is authorized by passing them.',
        '', '## Exit contributions','', '| Candidate | Reason | Trades | Net USDT |','| --- | --- | ---: | ---: |']
    ex=pd.DataFrame(exits)
    grouped=ex[(ex.pair=='ALL')&ex.strategy.isin(['LabBaseline',*CENTRAL])].groupby(['strategy','exit_reason'])[['trades','net_usdt']].sum()
    for (name,reason),r in grouped.iterrows(): lines.append(f'| {name} | {reason} | {int(r.trades)} | {fmt(r.net_usdt)} |')
    lines += ['', '## Limitations and artifacts','',
        'Hourly OHLCV execution is approximate. Fee is0.1% per side, already in trade outcomes; no additional slippage stress was run. Current exchange market metadata is not historically exact. Explicit gap fills may affect indicators. Annual boundary force exits are included. Small cells and correlated markets limit inference.',
        'Prefix and future-mutation checks test causality; no indicator uses future returns or centered windows. They do not establish an economic edge.',
        'Reports include all yearly/pair/variant metrics, exact commands and complete engine outputs. Full file inventory and hashes are retained. LabBaseline and Freqtrade core remain unchanged.']
    (HERE/'reports/comparison.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    verify_frozen()
    log('report_complete',eligible=[r['strategy'] for r in decisions if r['continue']],strategy_parameter_updates=0)
    print(core[['strategy','year','trades','net_usdt','profit_factor','wallet_drawdown_pct']].to_string(index=False))
    print(json.dumps(decisions,indent=2))


if __name__=='__main__': main()

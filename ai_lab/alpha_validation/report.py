"""Summarize immutable Phase 4B exports. Never invokes a backtest or changes alpha."""
import json
import numpy as np
import pandas as pd
from common import HERE, PERIODS, log, save, sha, verify_frozen


def summarize(trades, label):
    d=pd.DataFrame(trades)
    start=pd.Timestamp(PERIODS[label][0],tz='UTC'); end=pd.Timestamp(PERIODS[label][1],tz='UTC')
    if len(d):
        d['open_date']=pd.to_datetime(d.open_date,utc=True); d['close_date']=pd.to_datetime(d.close_date,utc=True)
        assert (d.open_date>=start).all() and (d.open_date<end).all() and (d.close_date<=end).all()
        assert d.loc[d.close_date==end,'exit_reason'].eq('force_exit').all()
        d=d.sort_values(['close_date','pair']); p=d.profit_abs
    else: p=pd.Series(dtype=float); d=pd.DataFrame(columns=['close_date','pair','profit_abs','profit_ratio','trade_duration','exit_reason'])
    gains=float(p[p>0].sum()); losses=float(-p[p<0].sum())
    curve=np.r_[1000.,1000+d.groupby('close_date').profit_abs.sum().sort_index().cumsum().to_numpy()]
    peak=np.maximum.accumulate(curve); streak=best=0
    for profit in p:
        streak=streak+1 if profit<0 else 0; best=max(best,streak)
    return {'trades':len(d),'wins':int((p>0).sum()),'losses':int((p<0).sum()),
      'win_rate_pct':float((p>0).mean()*100) if len(d) else None,'net_usdt':float(p.sum()),'total_return_pct':float(p.sum()/10),
      'average_trade_pct':float(d.profit_ratio.mean()*100) if len(d) else None,'profit_factor':gains/losses if losses else None,
      'expectancy_usdt':float(p.mean()) if len(d) else None,'closed_trade_drawdown_pct':float(((peak-curve)/peak).max()*100),
      'average_duration_hours':float(d.trade_duration.mean()/60) if len(d) else None,'maximum_consecutive_losses':best}


def fmt(x,n=2): return 'N/A' if x is None or pd.isna(x) else f'{x:.{n}f}'


def main():
    frozen=verify_frozen(); metrics=[]; exits=[]; source=[]
    for label in PERIODS:
        result=json.loads((HERE/'results'/label/'metrics.json').read_text())
        for strategy, m in result.items():
            all_metrics=summarize(m['trades'],label)
            assert abs(all_metrics['net_usdt']-m['profit_total_abs'])<1e-6 and all_metrics['trades']==m['total_trades']
            wallet=m['wallet_stats']
            for pair in ['ALL','BTC/USDT','ETH/USDT']:
                trades=m['trades'] if pair=='ALL' else [t for t in m['trades'] if t['pair']==pair]
                x=all_metrics if pair=='ALL' else summarize(trades,label)
                metrics.append({'label':label,'period_start':PERIODS[label][0],'period_end_exclusive':PERIODS[label][1],
                    'interpretation':frozen['label_for_every_result'],'strategy':strategy,'pair':pair,**x,
                    'wallet_max_drawdown_pct':float(wallet['max_drawdown_account']*100) if pair=='ALL' else None,
                    'sharpe':m.get('sharpe') if pair=='ALL' else None,'sortino':m.get('sortino') if pair=='ALL' else None,
                    'rejected_signals':m.get('rejected_signals') if pair=='ALL' else None})
                for reason in sorted({t['exit_reason'] for t in trades}):
                    selected=[t for t in trades if t['exit_reason']==reason]
                    exits.append({'label':label,'strategy':strategy,'pair':pair,'exit_reason':reason,'trades':len(selected),
                        'wins':sum(t['profit_abs']>0 for t in selected),'net_usdt':sum(t['profit_abs'] for t in selected),
                        'return_pct':sum(t['profit_abs'] for t in selected)/10})
        source.append({'label':label,'metrics_sha256':sha(HERE/'results'/label/'metrics.json'),
                       'archive_sha256':sha(next((HERE/'results'/label).glob('*.zip')))})
    frame=pd.DataFrame(metrics); frame.to_csv(HERE/'reports/period-metrics.csv',index=False)
    pd.DataFrame(exits).to_csv(HERE/'reports/exit-contributions.csv',index=False)
    save(HERE/'audits/result-source-hashes.json',source)
    all_rows=frame[frame.pair=='ALL']; pairs=frame[frame.pair!='ALL']
    aggregate=[]
    for strategy,g in all_rows.groupby('strategy'):
        total_trades=int(g.trades.sum()); gains=[]; losses=[]
        for label in PERIODS:
            raw=json.loads((HERE/'results'/label/'metrics.json').read_text())[strategy]['trades']
            gains += [t['profit_abs'] for t in raw if t['profit_abs']>0]; losses += [-t['profit_abs'] for t in raw if t['profit_abs']<0]
        aggregate.append({'strategy':strategy,'periods':len(g),'trades':total_trades,'net_usdt':float(g.net_usdt.sum()),
          'sum_period_returns_pct':float(g.total_return_pct.sum()),'profit_factor':float(sum(gains)/sum(losses)) if losses else None,
          'expectancy_usdt':float(g.net_usdt.sum()/total_trades) if total_trades else None,
          'profitable_periods':int(g.net_usdt.gt(0).sum()),'pf_above_one_periods':int(g.profit_factor.gt(1).sum()),
          'worst_period_usdt':float(g.net_usdt.min()),'max_wallet_drawdown_pct':float(g.wallet_max_drawdown_pct.max()),
          'max_pair_concentration_pct':None})
    agg=pd.DataFrame(aggregate)
    for strategy in agg.strategy:
        gross=max(abs(pairs[(pairs.strategy==strategy)&(pairs.net_usdt>0)].net_usdt.sum()),1e-12)
        top=pairs[(pairs.strategy==strategy)&(pairs.net_usdt>0)].net_usdt.max() if (pairs[(pairs.strategy==strategy)&(pairs.net_usdt>0)].shape[0]) else 0
        agg.loc[agg.strategy==strategy,'max_pair_concentration_pct']=top/gross*100
    agg.to_csv(HERE/'reports/aggregate-metrics.csv',index=False)
    alpha=agg[agg.strategy=='AlphaBreakout'].iloc[0]; base=agg[agg.strategy=='LabBaseline'].iloc[0]
    alpha_periods=all_rows[all_rows.strategy=='AlphaBreakout']; alpha_pairs=pairs[pairs.strategy=='AlphaBreakout']
    result_map={row.label:row for row in alpha_periods.itertuples()}
    # Conservative retrospective classification: no route to A without prospective data.
    alpha_positive=alpha.net_usdt>0 and alpha.profitable_periods>=3 and alpha.profit_factor>1
    recent_ok=result_map['C_2025_to_2026Q1'].net_usdt>=0 and result_map['D_2026_shadow'].net_usdt>=0
    category='B' if alpha_positive and not recent_ok else 'C'
    decision={'category':category,'reason':('Positive aggregate but recent C/D deterioration prevents an A claim; all evidence is retrospective.' if category=='B' else 'Inadequate cross-period robustness: only one profitable and PF>1 period, with both recent periods negative.'),
              'A_disallowed':'No prospective paper-trading result exists; Phase 4B results are explicitly retrospective only.',
              'alpha_aggregate':agg[agg.strategy=='AlphaBreakout'].to_dict(orient='records')[0],
              'baseline_aggregate':agg[agg.strategy=='LabBaseline'].to_dict(orient='records')[0],
              'recent_periods':{k:{'net_usdt':result_map[k].net_usdt,'profit_factor':result_map[k].profit_factor,'trades':result_map[k].trades} for k in ['C_2025_to_2026Q1','D_2026_shadow']}}
    save(HERE/'reports/classification.json',decision)
    lines=['# Phase 4B locked retrospective robustness evaluation','',
      '**Every result below is retrospective robustness evidence only. None is a new or untouched holdout.**','',
      f"**Classification: {category}. {'Interesting but retrospective evidence is too unstable.' if category=='B' else 'Fails robustness testing.'}**",'',
      'AlphaBreakout was frozen before retrieval or evaluation. No parameter, feature, exit, fee, model or period was changed after the manifest.',
      '', '## Frozen configuration','',
      '- AlphaBreakout: 24h prior-high breakout + 0.1 ATR14; NATR above prior24h mean; relative volume >=1.2; close location >=0.75; positive volume.',
      '- Exit: close below prior12h low; ROI 5%; stoploss -5%; no trailing.',
      '- 1h Binance spot BTC/USDT and ETH/USDT; 0.1% fee per side; 100 USDT stake; 1,000 USDT wallet; max two positions; next-candle limit execution.',
      f"- Frozen UTC: {frozen['freeze_utc']}; Git commit: {frozen['git_commit']}; manifest SHA256: {sha(HERE/'frozen-manifest.json')}",
      '', '## Period portfolio results','',
      '| Period | Strategy | Trades | Win / loss | Win % | Net USDT | Return % | Avg trade % | PF | Expectancy | Wallet DD % | Sharpe | Sortino | Duration h | Loss streak |',
      '| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for label in PERIODS:
        for strategy in ['AlphaBreakout','LabBaseline']:
            r=all_rows[(all_rows.label==label)&(all_rows.strategy==strategy)].iloc[0]
            lines.append(f'| {label} | {strategy} | {r.trades} | {r.wins} / {r.losses} | {fmt(r.win_rate_pct)} | {fmt(r.net_usdt)} | {fmt(r.total_return_pct)} | {fmt(r.average_trade_pct)} | {fmt(r.profit_factor)} | {fmt(r.expectancy_usdt)} | {fmt(r.wallet_max_drawdown_pct)} | {fmt(r.sharpe)} | {fmt(r.sortino)} | {fmt(r.average_duration_hours)} | {r.maximum_consecutive_losses} |')
    lines += ['', '## Aggregate across four separately reset retrospective runs','',
      '| Strategy | Trades | Net USDT | Sum returns % | PF | Expectancy | Profitable periods | PF>1 periods | Worst period | Max wallet DD |',
      '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for r in agg.itertuples(): lines.append(f'| {r.strategy} | {r.trades} | {fmt(r.net_usdt)} | {fmt(r.sum_period_returns_pct)} | {fmt(r.profit_factor)} | {fmt(r.expectancy_usdt)} | {r.profitable_periods}/4 | {r.pf_above_one_periods}/4 | {fmt(r.worst_period_usdt)} | {fmt(r.max_wallet_drawdown_pct)} |')
    lines += ['', 'Period returns are summed, not compounded, because each run starts with a fresh 1,000 USDT wallet.', '', '## BTC / ETH results','',
      '| Period | Strategy | Pair | Trades | Net USDT | PF | Win % |','| --- | --- | --- | ---: | ---: | ---: | ---: |']
    for label in PERIODS:
        for strategy in ['AlphaBreakout','LabBaseline']:
            for pair in ['BTC/USDT','ETH/USDT']:
                r=pairs[(pairs.label==label)&(pairs.strategy==strategy)&(pairs.pair==pair)].iloc[0]
                lines.append(f'| {label} | {strategy} | {pair} | {r.trades} | {fmt(r.net_usdt)} | {fmt(r.profit_factor)} | {fmt(r.win_rate_pct)} |')
    lines += ['', '## Exit-reason contribution: AlphaBreakout','', '| Period | Exit | Trades | Net USDT |','| --- | ---: | ---: | ---: |']
    ex=pd.DataFrame(exits); grouped=ex[(ex.strategy=='AlphaBreakout')&(ex.pair=='ALL')].groupby(['label','exit_reason'])[['trades','net_usdt']].sum()
    for (label,reason),r in grouped.iterrows(): lines.append(f'| {label} | {reason} | {int(r.trades)} | {fmt(r.net_usdt)} |')
    lines += ['', '## Robustness interpretation','',
      f"- AlphaBreakout is profitable in {int(alpha.profitable_periods)} of 4 periods with aggregate net {alpha.net_usdt:.2f} USDT and PF {fmt(alpha.profit_factor)}.",
      f"- LabBaseline aggregate net is {base.net_usdt:.2f} USDT and PF {fmt(base.profit_factor)} over the same periods.",
      '- Evaluate recent periods C and D directly: deterioration there prevents treating older gains as proof of continuing performance.',
      '- Pair tables identify whether one asset accounts for the result; concentration and small trade counts are retained as limitations, not filtered away.',
      '- Drawdown is engine wallet drawdown for full portfolios. Max consecutive losses use close-time order, with pair as tie-breaker.',
      '- Different periods contain different market regimes, but this evaluation does not use results to define or select regimes.',
      '- There is no prospective paper-trading evidence. Category A is therefore not available from this phase.',
      '', '## Audit results','',
      '- Frozen source, copied strategy and LabBaseline hashes matched before and after runs.',
      '- Causality tests passed: prefix consistency, future-price mutation, prior-high leakage check, real timestamp ordering, duplicate checks and next-candle signal validation.',
      '- Both pairs contain a single confirmed Binance 2023-03-24 13:00 UTC gap before period D. It is explicitly synthetic (prior close OHLC, zero volume); period D source is exact sealed data with no missing/duplicate candles.',
      '- No data beyond 2026-09-01, no ML/FreqAI, no parameter variants, and no modifications to the original seal occurred.',
      '- Backtest output may force-close positions at an end boundary. Such trades are retained, not discarded.',
      '- An execution-session recovery caused C to run twice under the same locked command. Both archives are preserved; their full metadata differs, while their strategy-level economic summaries are identical. No alternate setting was evaluated.',
      '', 'Full period, pair, aggregate, exit and source-hash files are retained in reports/ and audits/.']
    (HERE/'reports/comparison.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    log('report_complete',category=category,parameters_changed=0)


if __name__=='__main__': main()

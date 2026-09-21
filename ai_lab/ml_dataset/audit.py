"""Descriptive audit only; no fitting, feature selection or model training."""
import json
from pathlib import Path
import pandas as pd
from features import NUMERIC

HERE=Path(__file__).resolve().parent
TARGETS=['net_profit_ratio','profitable_after_fees','return_above_0_5_percent','return_above_1_percent','stoploss_hit','favorable_move_before_adverse_move']


def main():
    correlations=[]; balances=[]; pair_rows=[]; regime_rows=[]; suspicious=[]; redundant=[]
    distributions=[]
    for split in ['development','validation']:
        d=pd.read_parquet(HERE/f'data/{split}_dataset.parquet')
        for pair,g in [('ALL',d),*list(d.groupby('pair'))]:
            summary=g[NUMERIC].describe(percentiles=[.01,.05,.25,.5,.75,.95,.99]).T.reset_index(names='feature')
            summary['split']=split; summary['pair']=pair; distributions.append(summary)
            pair_rows.append({'split':split,'pair':pair,'rows':len(g),'win_rate_pct':g.profitable_after_fees.mean()*100,'mean_net_profit_ratio':g.net_profit_ratio.mean(),'median_duration_minutes':g.duration_minutes.median()})
        for target in TARGETS[1:]:
            s=d[target]; balances.append({'split':split,'target':target,'positive':int((s==1).sum()),'negative':int((s==0).sum()),'unknown':int(s.isna().sum()),'positive_pct_known':float(s.mean()*100)})
        for method in ['pearson','spearman']:
            for target in TARGETS:
                for feature in NUMERIC:
                    values=d[[feature,target]].dropna()
                    if values[feature].nunique()<2 or values[target].nunique()<2: continue
                    r=float(values[feature].corr(values[target],method=method))
                    row={'split':split,'feature':feature,'target':target,'method':method,'correlation':r,'n':len(values)}
                    correlations.append(row)
                    if abs(r)>=.95: suspicious.append(row)
        matrix=d[NUMERIC].corr()
        for i,a in enumerate(NUMERIC):
            for b in NUMERIC[i+1:]:
                r=matrix.loc[a,b]
                if pd.notna(r) and abs(r)>=.98: redundant.append({'split':split,'feature_a':a,'feature_b':b,'pearson':float(r)})
        for (pair,regime),g in d.groupby(['pair','regime']):
            regime_rows.append({'split':split,'pair':pair,'regime':regime,'rows':len(g),'win_rate_pct':g.profitable_after_fees.mean()*100,'mean_net_profit_ratio':g.net_profit_ratio.mean(),'mean_mfe_ratio':g.mfe_ratio.mean(),'mean_mae_ratio':g.mae_ratio.mean(),'mean_duration_minutes':g.duration_minutes.mean()})
    pd.concat(distributions).to_csv(HERE/'reports/feature-distributions.csv',index=False)
    pd.DataFrame(correlations).to_csv(HERE/'reports/feature-outcome-correlations.csv',index=False)
    pd.DataFrame(balances).to_csv(HERE/'reports/label-balance.csv',index=False)
    pd.DataFrame(pair_rows).to_csv(HERE/'reports/pair-comparison.csv',index=False)
    pd.DataFrame(regime_rows).to_csv(HERE/'reports/regime-outcomes.csv',index=False)
    (HERE/'audits/correlation-flags.json').write_text(json.dumps({'threshold_feature_outcome':.95,'suspicious_feature_outcome':suspicious,'threshold_feature_feature':.98,'redundant_feature_pairs':redundant},indent=2))
    lines=['# Phase 2C dataset audit','', 'Actual baseline trades only; no model trained and no features selected from correlations.',
           '', '| Split | Target | Positive | Negative | Unknown | Positive % of known |','| --- | --- | ---: | ---: | ---: | ---: |']
    for r in balances: lines.append(f"| {r['split']} | {r['target']} | {r['positive']} | {r['negative']} | {r['unknown']} | {r['positive_pct_known']:.2f} |")
    lines+=['','## Largest simple correlations with net profit ratio','','Within each split independently; Pearson correlations, exploratory only.','',
            '| Split | Feature | Pearson r | n |','| --- | --- | ---: | ---: |']
    for split in ['development','validation']:
        ranked=sorted([r for r in correlations if r['split']==split and r['target']=='net_profit_ratio' and r['method']=='pearson'],key=lambda r:abs(r['correlation']),reverse=True)[:5]
        for r in ranked: lines.append(f"| {split} | {r['feature']} | {r['correlation']:.4f} | {r['n']} |")
    lines+=['',f'Feature/outcome correlations with |r| >= 0.95: {len(suspicious)}.',f'Feature/feature pairs with |Pearson r| >= 0.98: {len(redundant)}; inspect correlation-flags.json.',
            'No flag is proof of absence of leakage; temporal construction and perturbation tests are separate checks.',
            '', '## Pair differences','','| Split | Pair | Rows | Win % | Mean net return % |','| --- | --- | ---: | ---: | ---: |']
    for r in pair_rows: lines.append(f"| {r['split']} | {r['pair']} | {r['rows']} | {r['win_rate_pct']:.2f} | {r['mean_net_profit_ratio']*100:.3f} |")
    lines+=['','## Regime-conditioned outcomes','','| Split | Pair | Regime | Rows | Win % | Mean net return % |','| --- | --- | --- | ---: | ---: | ---: |']
    for r in regime_rows: lines.append(f"| {r['split']} | {r['pair']} | {r['regime']} | {r['rows']} | {r['win_rate_pct']:.2f} | {r['mean_net_profit_ratio']*100:.3f} |")
    lines+=['','## Limits','', 'Small samples, overlapping trades and correlated indicators make these statistics exploratory.',
            'Scanning many correlations creates multiple-comparison risk. Validation is now inspected for descriptive analysis;',
            'using these findings to select future features would consume validation for selection, not final evaluation.',
            'Actual-trade selection is conditional on baseline signals and execution; these rows do not represent every market candle.',
            'Missing first-passage labels are explicitly ambiguous/censored, not losses. No unknown outcome is imputed.',
            'Raw ATR is price-scale dependent, so pooled relationships can be confounded by pair; pair-specific distributions are saved.',
            'No 2025+ outcomes, consumed test or sealed shadow data were loaded. See README.md for exact timing and excursion caveats.']
    (HERE/'reports/summary.md').write_text('\n'.join(lines)+'\n')
    print('\n'.join(lines[:39]))


if __name__=='__main__': main()

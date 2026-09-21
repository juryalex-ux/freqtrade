"""Describe frozen results; never refit or select a new model."""
import json
from pathlib import Path
import pandas as pd
import numpy as np

HERE=Path(__file__).resolve().parent


def main():
    cv=pd.read_csv(HERE/'results/development-mean-metrics.csv')
    val=pd.DataFrame(json.loads((HERE/'results/validation-metrics.json').read_text()))
    econ=pd.DataFrame(json.loads((HERE/'results/economics.json').read_text()))
    freeze=json.loads((HERE/'frozen-selection.json').read_text()); candidate=freeze['candidate']
    primary='profitable_after_fees'; metrics=['roc_auc','pr_auc_ap','balanced_accuracy','precision','recall','f1','brier','ece_5_bins']
    lines=['# Phase 3A conservative benchmark','',f"Development-frozen candidate: {candidate['model']} / {candidate['feature_set']}; primary threshold 0.50.",
           'PR-AUC is average precision, not trapezoidal interpolation. Zero-division precision/recall are reported as zero.',
           '', '## Development mean fold scores and Validation scores (primary target)','',
           '| Model | Features | CV ROC | CV AP | Validation ROC | AP | Balanced acc | Precision | Recall | F1 | Brier | ECE |',
           '| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for _,r in val[val.target==primary].iterrows():
        c=cv[(cv.target==primary)&(cv.model==r.model)&(cv.feature_set==r.feature_set)].iloc[0]
        lines.append(f"| {r.model} | {r.feature_set} | {c.roc_auc:.3f} | {c.pr_auc_ap:.3f} | {r.roc_auc:.3f} | {r.pr_auc_ap:.3f} | {r.balanced_accuracy:.3f} | {r.precision:.3f} | {r.recall:.3f} | {r.f1:.3f} | {r.brier:.3f} | {r.ece_5_bins:.3f} |")
    lines+=['','## Frozen candidate economics','','Subset of actual baseline trades, not a new Freqtrade backtest. No compounding or replacement opportunities.',
            'Drawdown uses closed subset profits on a 1,000-USDT starting basis, not mark-to-market wallet drawdown.',
            '', '| Split | Threshold | Selected | Retained % | Win % | Net USDT | Avg trade % | PF | Expectancy USDT | DD % | BTC USDT | ETH USDT |',
            '| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    selected=econ[(econ.target==primary)&(econ.model==candidate['model'])&(econ.feature_set==candidate['feature_set'])]
    def n(v): return 'N/A' if pd.isna(v) else f'{v:.3f}'
    for _,r in selected.iterrows():
        lines.append(f"| {r.split} | {r.threshold} | {r.trades} | {n(r.retained_pct)} | {n(r.win_rate_pct)} | {n(r.net_profit_usdt)} | {n(r.average_trade_pct)} | {n(r.profit_factor)} | {n(r.expectancy_usdt)} | {n(r.closed_subset_drawdown_pct)} | {n(r.btc_profit_usdt)} | {n(r.eth_profit_usdt)} |")
    lines+=['','Regime counts for every threshold are in economics.json and economics.csv; all candidates and secondary targets are retained there.',
            '', '## Metric leaders (descriptive, not post-validation selection)','']
    winners=[]
    for split,table in [('development_cv',cv),('validation',val)]:
        for target in table.target.unique():
            for metric in metrics:
                t=table[table.target==target].sort_values(metric,ascending=metric in ('brier','ece_5_bins'))
                r=t.iloc[0]; winners.append({'split':split,'target':target,'metric':metric,'model':r.model,'feature_set':r.feature_set,'value':float(r[metric])})
    pd.DataFrame(winners).to_csv(HERE/'reports/metric-leaders.csv',index=False)
    for r in winners:
        if r['target']==primary: lines.append(f"- {r['split']} {r['metric']}: {r['model']} / {r['feature_set']} = {r['value']:.4f}.")
    lines+=['','## Feature importance stability','', 'Held-out Development AP drop from permuting whole approximately weekly blocks; three repeats.',
            'Negative drops mean the perturbed feature performed better. Correlated features can mask each other.',
            'Permutation changes cross-feature relationships and is descriptive, not a causal intervention.','']
    imp=pd.read_csv(HERE/'results/block-permutation-importance.csv'); stability=[]; leaders=[]
    for (model,features),g in imp.groupby(['model','feature_set']):
        pivot=g.pivot(index='feature',columns='fold',values='ap_drop')
        ranks=pivot.corr(method='spearman'); off=[ranks.loc[a,b] for a in ranks for b in ranks if a<b and pd.notna(ranks.loc[a,b])]
        summary=g.groupby('feature').ap_drop.agg(['mean','std','min','max']).reset_index().sort_values('mean',ascending=False)
        for _,r in summary.iterrows(): leaders.append({'model':model,'feature_set':features,**r.to_dict()})
        value=float(np.mean(off)) if off else None; stability.append({'model':model,'feature_set':features,'mean_fold_rank_correlation':value})
        top=', '.join(f'{r.feature} ({r["mean"]:+.3f})' for _,r in summary.head(3).iterrows())
        lines.append(f'- {model}/{features}: fold rank agreement {n(value)}; top mean drops: {top}.')
    pd.DataFrame(stability).to_csv(HERE/'reports/importance-stability.csv',index=False)
    pd.DataFrame(leaders).to_csv(HERE/'reports/importance-summary.csv',index=False)
    co=pd.read_csv(HERE/'results/logistic-coefficients.csv')
    co.groupby(['feature_set','feature']).coefficient.agg(['mean','std','min','max']).to_csv(HERE/'reports/coefficient-stability.csv')
    lines+=['','Logistic coefficients are per training-fold standardized numeric feature or training-fitted one-hot category.',
            'Coefficient mean/std/min/max are saved separately; impurity importance is supplementary only.','',
            '## Regime ablation (all features minus no-regime)','', '| Model | CV AP delta | Validation AP delta | Validation ROC delta |', '| --- | ---: | ---: | ---: |']
    for model in ['dummy','logistic','forest','hist_gradient']:
        def row(table,s): return table[(table.target==primary)&(table.model==model)&(table.feature_set==s)].iloc[0]
        a,e=row(cv,'A_all'),row(cv,'E_no_regime'); av,ev=row(val,'A_all'),row(val,'E_no_regime')
        lines.append(f'| {model} | {a.pr_auc_ap-e.pr_auc_ap:+.4f} | {av.pr_auc_ap-ev.pr_auc_ap:+.4f} | {av.roc_auc-ev.roc_auc:+.4f} |')
    pair=pd.DataFrame(json.loads((HERE/'results/validation-pair-metrics.json').read_text()))
    lines+=['','## Frozen candidate by pair','','| Pair | n | ROC | AP | Precision | Recall | Brier |','| --- | ---: | ---: | ---: | ---: | ---: | ---: |']
    for _,r in pair[(pair.target==primary)&(pair.model==candidate['model'])&(pair.feature_set==candidate['feature_set'])].iterrows():
        lines.append(f'| {r.pair} | {r.n} | {r.roc_auc:.3f} | {r.pr_auc_ap:.3f} | {r.precision:.3f} | {r.recall:.3f} | {r.brier:.3f} |')
    ci=json.loads((HERE/'results/candidate-block-bootstrap.json').read_text())
    lines+=['','## Frozen candidate uncertainty','',ci['method'],'']
    for key,bounds in ci['intervals_95pct'].items(): lines.append(f'- {key}: 95% percentile interval [{bounds["low"]:.4f}, {bounds["high"]:.4f}].')
    lines+=['','Intervals condition on the Development selection and do not correct for trying multiple candidates.',
            'Only twelve calendar-month blocks exist; cross-month dependence and selection uncertainty limit inference.',
            'No IID trade bootstrap was used. No drawdown confidence interval is claimed.','',
            '## Full outputs','', 'All three targets, every fixed model and every feature set are in results/. Calibration bins and confusion matrices',
            'are retained in per-fold and Validation metrics JSON. Threshold economics includes BTC/ETH and regime distributions.',
            'A higher score or a reduction in losses caused by abstention does not alone establish a tradable edge.',
            'The consumed final test and sealed shadow were never opened. No Freqtrade strategy integration occurred.']
    (HERE/'reports/comparison.md').write_text('\n'.join(lines)+'\n')
    print('\n'.join(lines[:45]))


if __name__=='__main__': main()

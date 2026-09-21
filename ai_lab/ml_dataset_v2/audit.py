"""Descriptive audits of 2019–2024 examples. No ML or feature selection."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import ks_2samp
from feature_builder import NUMERIC

HERE=Path(__file__).resolve().parent
TARGETS=['profitable_after_fees','return_above_0_5_percent','return_above_1_percent','stoploss_hit']


def main():
    counts=[]; balance=[]; regimes=[]; correlations=[]; redundant=[]; drift=[]; pair_drift=[]; distributions=[]
    for name in ['A_portfolio','B_opportunities']:
        d=pd.read_parquet(HERE/f'data/{name}.parquet')
        for (year,pair),g in d.groupby(['year','pair']):
            counts.append({'dataset':name,'year':int(year),'pair':pair,'rows':len(g),'net_profit_usdt':float(g.net_profit_usdt.sum()),
                           'win_rate_pct':float(g.profitable_after_fees.mean()*100),'mean_trade_pct':float(g.net_profit_ratio.mean()*100),
                           'horizon_censored':int(g.horizon_censored.sum()),'forced_exits':int(g.boundary_forced_exit.sum())})
            desc=g[NUMERIC].describe(percentiles=[.05,.25,.5,.75,.95]).T.reset_index(names='feature')
            desc['dataset']=name; desc['year']=year; desc['pair']=pair; distributions.append(desc)
            for target in TARGETS:
                balance.append({'dataset':name,'year':int(year),'pair':pair,'target':target,'positive':int(g[target].sum()),'negative':int((g[target]==0).sum()),'positive_pct':float(g[target].mean()*100)})
            reference=d[(d.year==2019)&(d.pair==pair)]
            for feature in NUMERIC:
                a=reference[feature]; b=g[feature]; sd=a.std()
                drift.append({'dataset':name,'year':int(year),'pair':pair,'feature':feature,'reference_year':2019,
                              'standardized_mean_shift':float((b.mean()-a.mean())/sd) if sd>0 else None,
                              'ks_statistic':float(ks_2samp(a,b).statistic),'reference_n':len(a),'n':len(b)})
            for regime,h in g.groupby('regime'):
                regimes.append({'dataset':name,'year':int(year),'pair':pair,'regime':regime,'rows':len(h),'win_rate_pct':float(h.profitable_after_fees.mean()*100),
                                'mean_trade_pct':float(h.net_profit_ratio.mean()*100),'net_profit_usdt':float(h.net_profit_usdt.sum())})
        for year,g in [('ALL',d),*list(d.groupby('year'))]:
            for target in ['net_profit_ratio',*TARGETS,*[f'forward_{h}h_return' for h in [6,12,24,48]]]:
                for feature in NUMERIC:
                    values=g[[feature,target]].dropna()
                    if values[feature].nunique()<2 or values[target].nunique()<2: continue
                    for method in ['pearson','spearman']:
                        r=float(values[feature].corr(values[target],method=method))
                        correlations.append({'dataset':name,'year':str(year),'feature':feature,'target':target,'method':method,'r':r,'n':len(values)})
            matrix=g[NUMERIC].corr()
            for i,a in enumerate(NUMERIC):
                for b in NUMERIC[i+1:]:
                    r=matrix.loc[a,b]
                    if pd.notna(r) and abs(r)>=.98: redundant.append({'dataset':name,'year':str(year),'a':a,'b':b,'r':float(r)})
        for year,g in d.groupby('year'):
            for feature in NUMERIC:
                a=g[g.pair=='BTC/USDT'][feature]; b=g[g.pair=='ETH/USDT'][feature]
                pair_drift.append({'dataset':name,'year':int(year),'feature':feature,'btc_n':len(a),'eth_n':len(b),'ks_statistic':float(ks_2samp(a,b).statistic)})
    pd.DataFrame(counts).to_csv(HERE/'reports/rows-and-outcomes-by-year-pair.csv',index=False)
    pd.DataFrame(balance).to_csv(HERE/'reports/label-balance.csv',index=False)
    pd.DataFrame(regimes).to_csv(HERE/'reports/regime-outcomes.csv',index=False)
    pd.DataFrame(correlations).to_csv(HERE/'reports/feature-outcome-correlations.csv',index=False)
    pd.DataFrame(redundant,columns=['dataset','year','a','b','r']).to_csv(HERE/'audits/redundancy.csv',index=False)
    pd.DataFrame(drift).to_csv(HERE/'reports/year-feature-drift.csv',index=False)
    pd.DataFrame(pair_drift).to_csv(HERE/'reports/pair-feature-drift.csv',index=False)
    pd.concat(distributions).to_csv(HERE/'reports/feature-distributions.csv',index=False)
    flags=[r for r in correlations if abs(r['r'])>=.95]
    (HERE/'audits/suspicious-correlations.json').write_text(json.dumps({'threshold':.95,'flags':flags,'note':'Descriptive screen, not proof against leakage. Multiple dependent comparisons; no feature selection performed.'},indent=2))
    print('Rows and net outcomes by year:')
    c=pd.DataFrame(counts)
    print(c.groupby(['dataset','year'])[['rows','net_profit_usdt']].sum().to_string())
    print('Suspicious feature/outcome flags:',len(flags),'redundant pairs:',len(redundant))


if __name__=='__main__': main()

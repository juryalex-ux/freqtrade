"""Portfolio and independent-signal examples with explicit label intervals."""
import json,hashlib,heapq
from pathlib import Path
import numpy as np
import pandas as pd
from feature_builder import build_features,signal_mask,FEATURES,NUMERIC,DEFINITIONS,REMOVED,ADDED

HERE=Path(__file__).resolve().parent
START=pd.Timestamp('2019-01-01',tz='UTC'); END=pd.Timestamp('2025-01-01',tz='UTC')


def save(p,obj): p.write_text(json.dumps(obj,indent=2,default=str,allow_nan=False)+'\n')


def main():
    frames={}; tables={}; expected=set(); causal={}; signal_rows=[]
    for pair in ['BTC/USDT','ETH/USDT']:
        d=pd.read_feather(HERE/'data'/(pair.replace('/','_')+'-1h.feather'))
        assert d.date.max()<END and not d.date.duplicated().any()
        f=build_features(d); f['pair']=pair
        selected=(f.decision_time>=START)&(f.decision_time<END)&signal_mask(d)
        for i in d.index[selected]:
            expected.add((pair,f.decision_time.iloc[i]))
            signal_rows.append({'pair':pair,'signal_candle_open':str(d.date.iloc[i]),'decision_time':str(f.decision_time.iloc[i]),'synthetic':bool(d.synthetic.iloc[i])})
        columns=NUMERIC+['regime']; indices=set(range(743,len(d),809))
        for i in indices: pd.testing.assert_series_equal(build_features(d.iloc[:i+1]).iloc[-1][columns],f.iloc[i][columns])
        changed=d.copy(); cut=len(d)//2; changed.loc[cut:,['open','high','low','close']]*=3; changed.loc[cut:,'volume']*=9
        pd.testing.assert_frame_equal(build_features(changed).iloc[:cut][columns],f.iloc[:cut][columns])
        assert f.volatility_percentile_720.iloc[:719].isna().all()
        causal[pair]={'prefix_checks':len(indices),'future_mutation':'PASS','warmup_not_backfilled':'PASS'}
        frames[pair]=d; tables[pair]=f.set_index('decision_time',drop=False)
    pd.DataFrame(signal_rows).to_csv(HERE/'audits/all-entry-signals.csv',index=False)
    signal_metrics=json.loads((HERE/'results/opportunities/metrics.json').read_text())
    actual={(t['pair'],pd.Timestamp(t['open_date'])) for t in signal_metrics['trades']}
    assert expected==actual, f'Signal mismatch missing={expected-actual}, extra={actual-expected}'
    assert signal_metrics['rejected_signals']==0 and signal_metrics['timedout_entry_orders']==0
    save(HERE/'audits/signal-reconciliation.json',{'signals':len(expected),'independent_entries':len(actual),'missing':0,'extra':0,'rejected':0})
    sets={}; audit={}; manifests=[]
    for name,source in [('A_portfolio','portfolio'),('B_opportunities','opportunities')]:
        metrics=json.loads((HERE/f'results/{source}/metrics.json').read_text()); rows=[]
        for t in metrics['trades']:
            entry=pd.Timestamp(t['open_date']); exit=pd.Timestamp(t['close_date']); pair=t['pair']
            assert START<=entry<=exit<END
            f=tables[pair].loc[entry]; assert f.feature_candle_open<entry
            d=frames[pair]; i=int(d.index[d.date==f.feature_candle_open][0]); ratio=t['profit_ratio']
            r={'row_id':f'{pair}|{entry.isoformat()}','dataset':name,'year':entry.year,**f.to_dict(),
               'net_profit_ratio':ratio,'net_profit_usdt':t['profit_abs'],'profitable_after_fees':int(ratio>0),
               'return_above_0_5_percent':int(ratio>.005),'return_above_1_percent':int(ratio>.01),'stoploss_hit':int(t['exit_reason']=='stop_loss'),
               'exit_reason':t['exit_reason'],'duration_minutes':t['trade_duration'],
               'mfe_ratio':max(0,t['max_rate']/t['open_rate']-1),'mae_ratio':min(0,t['min_rate']/t['open_rate']-1),
               'strategy_outcome_end':exit,'boundary_forced_exit':int(t['exit_reason']=='force_exit')}
            for h in [6,12,24,48]:
                r[f'forward_{h}h_return']=float(d.close.iloc[i+h]/d.close.iloc[i]-1) if i+h<len(d) else np.nan
            r['label_end']=max(exit,entry+pd.Timedelta(hours=48))
            r['horizon_censored']=int(i+48>=len(d))
            rows.append(r)
        df=pd.DataFrame(rows).sort_values(['decision_time','pair']).reset_index(drop=True)
        assert not df.row_id.duplicated().any() and df.decision_time.is_monotonic_increasing
        assert not df[FEATURES].isna().any().any() and np.isfinite(df[NUMERIC].to_numpy(dtype=float)).all()
        assert abs(df.net_profit_usdt.sum()-metrics['profit_total_abs'])<1e-6
        df.to_parquet(HERE/f'data/{name}.parquet',index=False)
        meta=['row_id','dataset','year','decision_time','feature_candle_open']
        df[meta+FEATURES].to_csv(HERE/f'data/{name}_features.csv',index=False)
        df[meta+['pair']+[c for c in df if c not in meta+FEATURES]].to_csv(HERE/f'data/{name}_outcomes.csv',index=False)
        sets[name]=df
        active=[]; overlapping=0; max_active=0
        for r in df.itertuples():
            while active and active[0]<r.decision_time.value: heapq.heappop(active)
            overlapping+=int(bool(active)); heapq.heappush(active,r.label_end.value); max_active=max(max_active,len(active))
        audit[name]={'rows':len(df),'overlapping_label_rows':overlapping,'max_concurrent_label_intervals':max_active,'horizon_censored':int(df.horizon_censored.sum()),'boundary_force_exits':int(df.boundary_forced_exit.sum()),'duplicate_rows':0,'feature_nan':0}
        for year in range(2020,2025):
            a=pd.Timestamp(f'{year}-01-01',tz='UTC'); b=pd.Timestamp(f'{year+1}-01-01',tz='UTC'); cutoff=a-pd.Timedelta(hours=48)
            train=df[(df.decision_time<cutoff)&(df.label_end<cutoff)]
            test=df[(df.decision_time>=a)&(df.decision_time<b)&(df.label_end<b)]
            assert train.label_end.max()<test.decision_time.min()-pd.Timedelta(hours=48)
            assert set(train.row_id).isdisjoint(set(test.row_id))
            manifests.append({'dataset':name,'evaluation_year':year,'train_start':'2019-01-01','boundary':str(a),'test_end_exclusive':str(b),'embargo_hours':48,
                              'train_rows':len(train),'test_rows':len(test),'purged_train':int(((df.decision_time<a)&~df.row_id.isin(train.row_id)).sum()),
                              'right_boundary_test_exclusions':int(((df.decision_time>=a)&(df.decision_time<b)&~df.row_id.isin(test.row_id)).sum()),
                              'train_ids':train.row_id.tolist(),'test_ids':test.row_id.tolist()})
    # Shared entries must have identical frozen strategy outcomes under independent execution.
    joined=sets['A_portfolio'].merge(sets['B_opportunities'],on='row_id',suffixes=('_A','_B'))
    assert len(joined)==len(sets['A_portfolio'])
    for c in ['net_profit_ratio','duration_minutes','mfe_ratio','mae_ratio']: np.testing.assert_allclose(joined[c+'_A'],joined[c+'_B'],rtol=1e-9,atol=1e-9)
    assert (joined.exit_reason_A==joined.exit_reason_B).all()
    save(HERE/'audits/dataset-validation.json',{'causality':causal,'datasets':audit,'shared_outcomes_match':True,'feature_count':len(FEATURES),'numeric_features':len(NUMERIC),'no_2025_data':True})
    save(HERE/'folds.json',manifests)
    save(HERE/'schema.json',{'features':FEATURES,'numeric_features':NUMERIC,'definitions':DEFINITIONS,'removed_from_phase2c':REMOVED,'additions':ADDED,
                           'label_columns':[c for c in sets['A_portfolio'].columns if c not in FEATURES+meta],
                           'rules':'No forward return, outcome end, year, row_id, duration, profit, exit or label interval is a predictor. Pair/regime categorical. Future horizon returns labels only.'})
    print(json.dumps(audit,indent=2)); print('Features',len(FEATURES),'numeric',len(NUMERIC))


if __name__=='__main__': main()

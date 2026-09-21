"""One authorized shadow evaluation. Never refit or alter the candidate."""
import json
import os
import subprocess
import sys
import time
import zipfile

import joblib
import numpy as np
import pandas as pd
import requests
from common import HERE, ROOT, guard, sha, save, log, now, build_features, NUMERIC, classification as classify, economics

PAIRS=['BTC/USDT','ETH/USDT']
START=pd.Timestamp('2026-04-01',tz='UTC')
END=pd.Timestamp('2026-09-01',tz='UTC')
WARM=pd.Timestamp('2026-03-01',tz='UTC')


def warmup(pair):
    rows=[]; cursor=int(WARM.timestamp()*1000); end=int(START.timestamp()*1000)
    while cursor<end:
        params={'symbol':pair.replace('/',''),'interval':'1h','startTime':cursor,'endTime':end-1,'limit':1000}
        log('warmup_request',pair=pair,params=params)
        for attempt in range(3):
            try:
                response=requests.get('https://api.binance.com/api/v3/klines',params=params,timeout=45)
                response.raise_for_status(); batch=response.json(); break
            except requests.RequestException:
                if attempt==2: raise
                time.sleep(2)
        if not batch: break
        rows+=batch; cursor=int(batch[-1][0])+3600000
    d=pd.DataFrame([[r[0],*r[1:6]] for r in rows],columns=['date','open','high','low','close','volume'])
    d['date']=pd.to_datetime(d.date,unit='ms',utc=True)
    for c in ['open','high','low','close','volume']: d[c]=d[c].astype(float)
    assert d.date.is_monotonic_increasing and d.date.is_unique
    assert d.date.min()>=WARM and d.date.max()<START
    d.to_feather(HERE/'warmup'/f"{pair.replace('/','_')}-raw.feather")
    grid=pd.date_range(WARM,START,freq='h',inclusive='left')
    indexed=d.set_index('date').reindex(grid)
    missing=indexed.close.isna()
    assert not missing.iloc[0] and int(missing.sum())<=12, 'Incomplete March warmup; stop without tuning'
    past=indexed.close.ffill()
    for c in ['open','high','low','close']: indexed.loc[missing,c]=past[missing]
    indexed.loc[missing,'volume']=0
    indexed['synthetic']=missing
    log('warmup_complete',pair=pair,observed=len(d),synthetic=int(missing.sum()),excluded_from_fitting=True)
    return indexed.reset_index(names='date')


def main():
    guard()
    assert not (HERE/'EVALUATION_STARTED.json').exists(), 'Single-shot evaluation already started; no automatic rerun'
    assert not (HERE/'CONSUMED.json').exists(), 'Shadow already consumed'
    frozen=json.loads((HERE/'frozen-candidate.json').read_text())
    hashes=json.loads((HERE/'pre-unseal-hashes.json').read_text())
    for relative,digest in hashes['source_hashes'].items(): assert sha(ROOT/relative)==digest,relative
    for name,digest in hashes['hashes'].items(): assert sha(HERE/name)==digest,name
    assert frozen['threshold']==.55 and frozen['target']=='profitable_after_fees'
    save(HERE/'EVALUATION_STARTED.json',{'utc':now(),'manifest_sha256':sha(HERE/'frozen-candidate.json'),
        'rule':'Evaluation started; do not run alternate settings or overwrite evidence.'})
    log('unseal_authorized_after_freeze',manifest_sha256=sha(HERE/'frozen-candidate.json'))
    sealpath=ROOT/'ai_lab/regime/shadow/SEALED.json'
    seal=json.loads(sealpath.read_text())
    original={sealpath:sha(sealpath)}
    assert seal['status']=='SEALED_UNEVALUATED'
    assert pd.Timestamp(seal['start_utc'])==START and pd.Timestamp(seal['end_exclusive_utc'])==END
    tables={}; audits={}
    for folder in ['warmup','engine_data','backtest']:(HERE/folder).mkdir(exist_ok=True)
    for pair in PAIRS:
        record=next(x for x in seal['files'] if x['pair']==pair)
        path=(ROOT/'ai_lab/regime'/record['file']).resolve()
        assert path.is_relative_to((ROOT/'ai_lab/regime/shadow').resolve())
        assert sha(path)==record['sha256'],'Sealed price hash mismatch'
        original[path]=sha(path)
        prices=pd.read_feather(path)
        grid=pd.date_range(START,END,freq='h',inclusive='left')
        assert pd.DatetimeIndex(prices.date).equals(grid)
        assert len(prices)==record['candles'] and prices.date.is_unique
        assert np.isfinite(prices[['open','high','low','close','volume']].to_numpy()).all()
        assert (prices[['open','high','low','close']]>0).all().all() and (prices.volume>=0).all()
        prices['synthetic']=False
        full=pd.concat([warmup(pair),prices],ignore_index=True)
        features=build_features(full); features['pair']=pair
        columns=NUMERIC+['regime']
        indices=list(range(743,len(full),337))+[len(full)-1]
        for i in indices:
            pd.testing.assert_series_equal(build_features(full.iloc[:i+1]).iloc[-1][columns],features.iloc[i][columns])
        cut=len(full)//2; changed=full.copy()
        changed.loc[cut:,['open','high','low','close']]*=3
        changed.loc[cut:,'volume']*=7
        pd.testing.assert_frame_equal(build_features(changed).iloc[:cut][columns],features.iloc[:cut][columns])
        assert features.volatility_percentile_720.iloc[:719].isna().all()
        tables[pair]=features.set_index('decision_time',drop=False)
        full[['date','open','high','low','close','volume']].to_feather(HERE/'engine_data'/f"{pair.replace('/','_')}-1h.feather")
        audits[pair]={'sealed_candles':len(prices),'prefix_checks':len(indices),'future_mutation':'PASS',
                      'no_future_fill':'PASS','missing_shadow_candles':0,'duplicate_candles':0}
        log('shadow_features_ready',pair=pair,**audits[pair])
    save(HERE/'original-seal-hashes.json',{p.relative_to(ROOT).as_posix():h for p,h in original.items()})
    cmd=[sys.executable,'-B','-m','freqtrade','backtesting','--config','ai_lab/configs/backtest.json',
         '--userdir',str(HERE),'--datadir',str(HERE/'engine_data'),'--strategy','LabBaseline',
         '--strategy-path','ai_lab/strategies','--timerange','20260401-20260901','--fee','0.001',
         '--cache','none','--export','trades','--backtest-directory',str(HERE/'backtest')]
    save(HERE/'backtest/command.json',cmd)
    log('baseline_backtest_start',command=cmd)
    with (HERE/'backtest/output.log').open('w',encoding='utf-8') as out:
        subprocess.run(cmd,cwd=ROOT,stdout=out,stderr=subprocess.STDOUT,check=True,
                       env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
    archive=next((HERE/'backtest').glob('*.zip'))
    with zipfile.ZipFile(archive) as z:
        name=next(x for x in z.namelist() if x.endswith('.json') and not x.endswith('_config.json'))
        baseline=json.loads(z.read(name))['strategy']['LabBaseline']
    save(HERE/'backtest/metrics.json',baseline)
    rows=[]
    for trade in baseline['trades']:
        entry=pd.Timestamp(trade['open_date']); close=pd.Timestamp(trade['close_date'])
        assert START<=entry<=close<END
        feature=tables[trade['pair']].loc[entry]
        assert feature.feature_candle_open+pd.Timedelta(hours=1)==entry
        rows.append({**feature.to_dict(),'row_id':f"{trade['pair']}|{entry.isoformat()}",
            'strategy_outcome_end':close,'net_profit_ratio':trade['profit_ratio'],'net_profit_usdt':trade['profit_abs'],
            'profitable_after_fees':int(trade['profit_ratio']>0),'duration_minutes':trade['trade_duration'],
            'exit_reason':trade['exit_reason']})
    d=pd.DataFrame(rows).sort_values(['decision_time','pair']).reset_index(drop=True)
    cols=frozen['features']
    assert len(d)>0 and d.row_id.is_unique and not d[cols].isna().any().any()
    assert np.isfinite(d[[c for c in cols if c not in ['pair','regime']]].to_numpy(dtype=float)).all()
    assert abs(d.net_profit_usdt.sum()-baseline['profit_total_abs'])<1e-7
    d.to_parquet(HERE/'shadow-examples.parquet',index=False)
    pipeline=joblib.load(HERE/'candidate.joblib')
    assert sha(HERE/'candidate.joblib')==hashes['hashes']['candidate.joblib']
    log('single_prediction_call',rows=len(d),threshold=.55)
    probabilities=pipeline.predict_proba(d[cols])[:,1]  # Exactly one call; no model refit.
    d['probability']=probabilities; d['selected']=probabilities>=.55
    d.to_csv(HERE/'shadow-predictions.csv',index=False)
    d.to_parquet(HERE/'shadow-predictions.parquet',index=False)
    # Preserve original seal and prices byte-for-byte. Consumption is a separate append-only marker.
    save(HERE/'CONSUMED.json',{'status':'CONSUMED','utc':now(),
        'original_seal':'ai_lab/regime/shadow/SEALED.json','original_seal_sha256':original[sealpath],
        'evaluation':'2026-04-01 through 2026-09-01 exclusive',
        'candidate_manifest_sha256':sha(HERE/'frozen-candidate.json'),
        'prediction_sha256':sha(HERE/'shadow-predictions.parquet'),
        'rule':'Never treat this period as unseen again. Original SEALED.json is historical and is not resealed.'})
    classification={'ALL':classify(d.profitable_after_fees,probabilities)}
    economic={'unfiltered':economics(d),'filtered':economics(d[d.selected]),'pairs':{}}
    for pair in PAIRS:
        part=d[d.pair==pair]
        classification[pair]=classify(part.profitable_after_fees,part.probability)
        economic['pairs'][pair]={'unfiltered':economics(part),'filtered':economics(part[part.selected])}
        economic['pairs'][pair]['filtered']['retention_pct']=float(part.selected.mean()*100)
    economic['filtered']['retention_pct']=float(d.selected.mean()*100)
    economic['unfiltered']['retention_pct']=100.
    economic['unfiltered']['freqtrade_wallet_max_drawdown_pct']=baseline['max_drawdown_account']*100
    economic['net_improvement_usdt']=economic['filtered']['net_usdt']-economic['unfiltered']['net_usdt']
    score=classification['ALL']; result=economic['filtered']
    ranking=score['roc_auc'] is not None and score['roc_auc']>.5 and score['pr_auc_ap']>score['prevalence']
    profitable=result['net_usdt']>0 and economic['net_improvement_usdt']>0
    strong=ranking and score['roc_auc']>=.55 and score['pr_auc_ap']>=score['prevalence']+.05 and profitable
    strong=strong and result['profit_factor'] is not None and result['profit_factor']>=1.2 and result['trades']>=30
    strong=strong and all(v['filtered']['trades']>=10 and v['filtered']['net_usdt']>=0 for v in economic['pairs'].values())
    category='A' if strong else 'B' if ranking and profitable else 'C'
    save(HERE/'classification.json',classification)
    save(HERE/'economics.json',economic)
    for path,digest in original.items(): assert sha(path)==digest,'Original shadow modified'
    for relative,digest in hashes['source_hashes'].items(): assert sha(ROOT/relative)==digest,relative
    for name,digest in hashes['hashes'].items(): assert sha(HERE/name)==digest,name
    guard()
    save(HERE/'evaluation-audit.json',{'utc':now(),'category':category,'all_integrity_checks':'PASS',
        'original_seal_and_prices_unchanged':True,'pre_unseal_candidate_hashes_unchanged':True,
        'source_hashes_unchanged':True,'prediction_calls':1,'shadow_refits':0,
        'training_rows':1271,'training_years':list(range(2019,2025)),
        'causality':audits,'trade_rows':len(d),'selected_rows':int(d.selected.sum()),
        'duplicates':0,'nonfinite_features':0,'future_entry_features':0,
        'feature_count':len(cols),'forced_boundary_exits':int(d.exit_reason.eq('force_exit').sum()),
        'rejected_baseline_signals':baseline['rejected_signals'],
        'drawdown_definition':'Close-time closed-trade subset equity; original Phase 3C used entry-day ordering, corrected and frozen before unseal.',
        'category_policy':'Predeclared in frozen-candidate.json; no performance-selected threshold or feature changes'})
    log('evaluation_complete',category=category,selected=int(d.selected.sum()),original_seal_unchanged=True)
    print(json.dumps({'classification':classification,'economics':economic},indent=2))


if __name__=='__main__':
    try: main()
    except Exception as error:
        log('evaluation_error',type=type(error).__name__,message=str(error))
        raise

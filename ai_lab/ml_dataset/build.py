"""Build actual-trade datasets; only 2023/2024 source paths are allowed."""
import hashlib,json,subprocess,sys
from pathlib import Path
import numpy as np
import pandas as pd
from features import build_features,FEATURES,NUMERIC,DEFINITIONS

HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'ai_lab/regime'))
from analyze import load_pair


def save(path,obj): path.write_text(json.dumps(obj,indent=2,default=str,allow_nan=False)+'\n')
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def first_passage(trade,candles):
    # Exclude the exit candle: its high/low may have happened after the fill.
    period=candles[(candles.date>=pd.Timestamp(trade['open_date'])) & (candles.date<pd.Timestamp(trade['close_date']))]
    favorable=period.loc[period.high>=trade['open_rate']*1.01,'date']
    adverse=period.loc[period.low<=trade['open_rate']*.99,'date']
    f=favorable.iloc[0] if len(favorable) else None; a=adverse.iloc[0] if len(adverse) else None
    if f is None and a is None: return None,'neither_barrier_observed'
    if f is not None and a is not None and f==a: return None,'same_hour_ambiguous'
    return int(a is None or (f is not None and f<a)),'observed_order'


def main():
    assert subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()=='ai-lab-development'
    expected=json.loads((ROOT/'ai_lab/evaluation/protocol.json').read_text())['strategy_sha256']
    assert sha(ROOT/'ai_lab/strategies/LabBaseline.py')==expected
    sources={}; candles={}; feature_tables={}; checks={}
    for pair in ['BTC/USDT','ETH/USDT']:
        d,audit=load_pair(pair)  # Reader strictly clips Dec2022 warmup through Dec2024.
        candles[pair]=d; f=build_features(d); f['pair']=pair
        feature_tables[pair]=f.set_index('decision_time',drop=False); sources[pair]=audit
        indices=set(range(743,len(d),251))
        cols=NUMERIC+['regime']
        for i in indices:
            pd.testing.assert_series_equal(build_features(d.iloc[:i+1]).iloc[-1][cols],f.iloc[i][cols])
        cut=len(d)//2; changed=d.copy()
        changed.loc[cut:,['open','high','low','close']]*=4; changed.loc[cut:,'volume']*=17
        pd.testing.assert_frame_equal(build_features(changed).iloc[:cut][cols],f.iloc[:cut][cols])
        checks[pair]={'prefixes':len(indices),'future_mutation':'PASS'}
    schema={'feature_columns':FEATURES,'numeric_feature_columns':NUMERIC,'definitions':DEFINITIONS,
            'metadata':['row_id','pair','split','decision_time','feature_candle_open'],
            'label_columns':['net_profit_ratio','win_loss','mfe_ratio','mae_ratio','duration_minutes','exit_reason','profitable_after_fees','return_above_0_5_percent','return_above_1_percent','stoploss_hit','favorable_move_before_adverse_move','first_passage_status'],
            'feature_time_rule':'Use candle t-1h for decision at t; no entry fill or outcome data in features.',
            'mfe_mae':'Engine-exported max_rate/open_rate-1 (clamped >=0) and min_rate/open_rate-1 (clamped <=0). Gross price excursions, not after-fee returns; engine candle-resolution estimates.',
            'first_passage':'First +1% gross high barrier before -1% low barrier during [entry,exit); same-hour tie or neither barrier => null. Exit candle excluded to avoid post-exit price leakage into label. Intrabar ordering is not claimed.',
            'selection':'Actual baseline trades only; no rejected/opportunity counterfactuals. No models trained.'}
    save(HERE/'schema.json',schema)
    counts={}; rows_all=[]
    for split,start,end in [('development','2023-01-01','2024-01-01'),('validation','2024-01-01','2025-01-01')]:
        path=ROOT/f'ai_lab/evaluation/results/{split}/metrics.json'; sources[split]={'path':str(path),'sha256':sha(path)}
        original=json.loads(path.read_text()); records=[]; outcomes=[]
        for trade in original['trades']:
            entry=pd.Timestamp(trade['open_date']); pair=trade['pair']; close=pd.Timestamp(trade['close_date'])
            assert pd.Timestamp(start,tz='UTC')<=entry<=close<pd.Timestamp(end,tz='UTC')
            feature=feature_tables[pair].loc[entry]
            assert feature.feature_candle_open+pd.Timedelta(hours=1)==entry
            row_id=f'{split}|{pair}|{entry.isoformat()}'
            records.append({'row_id':row_id,'split':split,**feature.to_dict()})
            first,status=first_passage(trade,candles[pair]); profit=trade['profit_ratio']
            outcomes.append({'row_id':row_id,'decision_time':entry,'pair':pair,'split':split,'outcome_end':close,
                'net_profit_ratio':profit,'win_loss':'win' if profit>0 else ('loss' if profit<0 else 'flat'),
                'mfe_ratio':max(0,trade['max_rate']/trade['open_rate']-1),'mae_ratio':min(0,trade['min_rate']/trade['open_rate']-1),
                'duration_minutes':trade['trade_duration'],'exit_reason':trade['exit_reason'],'profitable_after_fees':int(profit>0),
                'return_above_0_5_percent':int(profit>.005),'return_above_1_percent':int(profit>.01),
                'stoploss_hit':int(trade['exit_reason'] in ('stop_loss','trailing_stop_loss','stoploss_on_exchange')),
                'favorable_move_before_adverse_move':first,'first_passage_status':status})
        f=pd.DataFrame(records).sort_values(['decision_time','pair']).reset_index(drop=True)
        y=pd.DataFrame(outcomes).sort_values(['decision_time','pair']).reset_index(drop=True)
        assert not f.row_id.duplicated().any() and not f[['decision_time','pair']].duplicated().any()
        assert f.decision_time.is_monotonic_increasing
        assert not f[FEATURES].isna().any().any(), 'Missing feature; no backfill is allowed'
        assert np.isfinite(f[NUMERIC].to_numpy(dtype=float)).all()
        assert not set(schema['label_columns']) & set(f.columns)
        joined=f.merge(y.drop(columns=['decision_time','pair','split']),on='row_id',validate='one_to_one')
        f.to_csv(HERE/f'data/{split}_features.csv',index=False); y.to_csv(HERE/f'data/{split}_outcomes.csv',index=False)
        joined.to_parquet(HERE/f'data/{split}_dataset.parquet',index=False)
        rows_all.append(joined); counts[split]=len(f)
    assert rows_all[0].outcome_end.max()<rows_all[1].decision_time.min()
    assert set(rows_all[0].row_id).isdisjoint(set(rows_all[1].row_id))
    save(HERE/'audits/validation.json',{'counts':counts,'feature_count':len(FEATURES),'numeric_count':len(NUMERIC),'checks':checks,'duplicates':0,'feature_nan_count':0,'feature_infinity_count':0,'chronological_order':'PASS','split_and_outcome_separation':'PASS','baseline_hash':expected})
    save(HERE/'audits/source-manifest.json',sources)
    print(json.dumps(counts)); print('Features:',len(FEATURES))


if __name__=='__main__': main()

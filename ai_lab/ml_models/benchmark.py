"""Small locked time-series benchmark. Only 2023/2024 datasets are read."""
import os
os.environ.setdefault('OMP_NUM_THREADS','1')
os.environ.setdefault('OPENBLAS_NUM_THREADS','1')
import hashlib,json,subprocess
from pathlib import Path
from datetime import datetime,timezone
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler,OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier,HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score,average_precision_score,balanced_accuracy_score,precision_score,recall_score,f1_score,brier_score_loss,confusion_matrix

HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[1]
SCHEMA=json.loads((ROOT/'ai_lab/ml_dataset/schema.json').read_text())
ALL=SCHEMA['feature_columns']
REMOVED={'body_ratio':'Nearly duplicate of return_1h; candle opens approximately prior close.',
         'atr14':'Price-scale dependent duplicate of normalized ATR multiplied by price.',
         'macd_hist_ratio':'Exact difference of macd_ratio and macd_signal_ratio.',
         'source_synthetic':'Constant zero among Development trades; no predictive variation.'}
PRICE=[x for x in ALL if x.startswith(('ema','return_')) and not x.startswith('return_std')]+['trend_efficiency_20','body_ratio','range_ratio','body_to_range','close_location','distance_high_24','distance_low_24','distance_high_168','distance_low_168','candles_since_prior_signal','pair']
VOL=['atr14','natr14','return_std_24','return_std_168','volatility_percentile_720']
SETS={'A_all':ALL,'B_reduced':[x for x in ALL if x not in REMOVED],'C_price':PRICE,
      'D_price_volatility':PRICE+VOL,'E_no_regime':[x for x in ALL if x not in ('regime','regime_duration','regime_transition')]}
TARGETS=['profitable_after_fees','return_above_0_5_percent','return_above_1_percent']
MODELS=['dummy','logistic','forest','hist_gradient']
THRESHOLDS=[.50,.55,.60,.65,.70]
FOLDS=[('2023-04-01','2023-07-01'),('2023-07-01','2023-10-01'),('2023-10-01','2024-01-01')]
SEED=31415


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v): p.write_text(json.dumps(v,indent=2,default=str,allow_nan=False)+'\n')
def utc(s): return pd.Timestamp(s,tz='UTC')


def pipeline(name,columns):
    categorical=[c for c in columns if c in ('pair','regime')]
    numeric=[c for c in columns if c not in categorical]
    prep=ColumnTransformer([('numeric',StandardScaler(),numeric),('category',OneHotEncoder(handle_unknown='ignore',sparse_output=False),categorical)])
    models={'dummy':DummyClassifier(strategy='prior'),
            'logistic':LogisticRegression(C=.1,solver='lbfgs',max_iter=2000,random_state=SEED),
            'forest':RandomForestClassifier(n_estimators=100,max_depth=3,min_samples_leaf=15,max_features='sqrt',bootstrap=False,n_jobs=1,random_state=SEED),
            'hist_gradient':HistGradientBoostingClassifier(max_iter=60,learning_rate=.05,max_leaf_nodes=7,max_depth=3,min_samples_leaf=15,l2_regularization=10,early_stopping=False,random_state=SEED)}
    return Pipeline([('preprocess',prep),('model',models[name])])


def scores(y,p):
    y=np.asarray(y); p=np.asarray(p); predicted=p>=.5
    bins=[]; ece=0
    for lo,hi in zip(np.arange(0,1,.2),np.arange(.2,1.01,.2)):
        mask=(p>=lo)&(p<(hi if hi<.999 else 1.00001))
        if mask.any():
            actual=float(y[mask].mean()); mean=float(p[mask].mean()); count=int(mask.sum())
            bins.append({'lower':float(lo),'upper':float(hi),'n':count,'mean_probability':mean,'observed_rate':actual})
            ece+=count/len(y)*abs(actual-mean)
    return {'roc_auc':float(roc_auc_score(y,p)) if len(np.unique(y))==2 else None,
            'pr_auc_ap':float(average_precision_score(y,p)), 'balanced_accuracy':float(balanced_accuracy_score(y,predicted)),
            'precision':float(precision_score(y,predicted,zero_division=0)), 'recall':float(recall_score(y,predicted,zero_division=0)),
            'f1':float(f1_score(y,predicted,zero_division=0)),'brier':float(brier_score_loss(y,p)),
            'ece_5_bins':ece,'mean_probability':float(p.mean()),'prevalence':float(y.mean()),
            'confusion_matrix':confusion_matrix(y,predicted,labels=[0,1]).tolist(),'calibration':bins,'n':len(y)}


def economic(d,mask):
    chosen=d.loc[np.asarray(mask)]; profits=chosen.net_profit_usdt
    losses=-profits[profits<0].sum(); wins=profits[profits>0].sum()
    equity=np.r_[1000,1000+chosen.groupby('outcome_end').net_profit_usdt.sum().sort_index().cumsum().to_numpy()]
    peak=np.maximum.accumulate(equity)
    return {'trades':len(chosen),'retained_pct':len(chosen)/len(d)*100,
            'win_rate_pct':float((profits>0).mean()*100) if len(chosen) else None,'net_profit_usdt':float(profits.sum()),
            'return_pct':float(profits.sum()/10),'average_trade_pct':float(chosen.net_profit_ratio.mean()*100) if len(chosen) else None,
            'profit_factor':float(wins/losses) if losses>0 else None,'expectancy_usdt':float(profits.mean()) if len(chosen) else None,
            'closed_subset_drawdown_pct':float(((peak-equity)/peak).max()*100),
            'btc_profit_usdt':float(chosen.loc[chosen.pair=='BTC/USDT','net_profit_usdt'].sum()),
            'eth_profit_usdt':float(chosen.loc[chosen.pair=='ETH/USDT','net_profit_usdt'].sum()),
            'regime_counts':{str(k):int(v) for k,v in chosen.regime.value_counts().items()}}


def load(split):
    assert split in ('development','validation')
    d=pd.read_parquet(ROOT/f'ai_lab/ml_dataset/data/{split}_dataset.parquet').sort_values(['decision_time','pair']).reset_index(drop=True)
    metrics=json.loads((ROOT/f'ai_lab/evaluation/results/{split}/metrics.json').read_text())
    profit={(t['pair'],pd.Timestamp(t['open_date'])):t['profit_abs'] for t in metrics['trades']}
    d['net_profit_usdt']=[profit[(r.pair,r.decision_time)] for r in d.itertuples()]
    assert abs(d.net_profit_usdt.sum()-metrics['profit_total_abs'])<1e-7
    start,end=('2023-01-01','2024-01-01') if split=='development' else ('2024-01-01','2025-01-01')
    assert (d.decision_time>=utc(start)).all() and (d.outcome_end<utc(end)).all()
    assert (d.feature_candle_open+pd.Timedelta(hours=1)<=d.decision_time).all()
    assert not d.row_id.duplicated().any() and not d[ALL].isna().any().any()
    return d


def permutation(model,x,y,fold,model_name,set_name):
    """Permute whole contiguous ~7-day blocks, not isolated observations."""
    rng=np.random.default_rng(SEED+fold); base=average_precision_score(y,model.predict_proba(x)[:,1]); result=[]
    groups=x.index.to_series().groupby(x.attrs['dates'].dt.floor('7D').to_numpy()).apply(list).tolist()
    if len(groups)<2: return result
    for column in x.columns:
        deltas=[]
        for _ in range(3):
            order=np.concatenate([groups[i] for i in rng.permutation(len(groups))])
            changed=x.copy(); changed[column]=x.loc[order,column].to_numpy()
            deltas.append(float(base-average_precision_score(y,model.predict_proba(changed)[:,1])))
        result.append({'fold':fold,'model':model_name,'feature_set':set_name,'feature':column,'ap_drop':float(np.mean(deltas))})
    return result


def main():
    assert subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()=='ai-lab-development'
    expected=json.loads((ROOT/'ai_lab/evaluation/protocol.json').read_text())['strategy_sha256']
    assert sha(ROOT/'ai_lab/strategies/LabBaseline.py')==expected
    assert not (HERE/'results/validation_consumed.json').exists(), 'Benchmark already complete; do not adapt to validation'
    protocol={'targets':TARGETS,'feature_sets':SETS,'removed':REMOVED,'folds':FOLDS,'primary_threshold':.5,'sensitivity_thresholds':THRESHOLDS,
              'selection':'Primary-target candidate maximizing mean Development fold AP; fixed configurations only. No validation selection. Economics required before any usefulness claim.',
              'models':{name:pipeline(name,ALL).named_steps['model'].get_params() for name in MODELS},
              'early_stopping':'Disabled: fixed60 iterations avoids sklearn random internal holdout.',
              'purge':'Training outcome_end strictly before next test decision boundary; split all pairs at same calendar boundary.',
              'seed':SEED,'script_sha256':sha(Path(__file__)),'created_utc':datetime.now(timezone.utc).isoformat()}
    save(HERE/'protocol.json',protocol)
    d=load('development'); assert d.source_synthetic.nunique()==1
    fold_info=[]; fold_scores=[]; predictions=[]; importances=[]; coefficients=[]; impurity=[]
    for fi,(start,end) in enumerate(FOLDS,1):
        train=d[(d.decision_time<utc(start))&(d.outcome_end<utc(start))]
        test=d[(d.decision_time>=utc(start))&(d.decision_time<utc(end))]
        assert train.outcome_end.max()<test.decision_time.min()
        fold_info.append({'fold':fi,'train':len(train),'test':len(test),'purged':int(((d.decision_time<utc(start))&(d.outcome_end>=utc(start))).sum()),'last_training_outcome':str(train.outcome_end.max()),'first_test_decision':str(test.decision_time.min())})
        for target in TARGETS:
            for set_name,columns in SETS.items():
                for name in MODELS:
                    model=pipeline(name,columns); model.fit(train[columns],train[target]); p=model.predict_proba(test[columns])[:,1]
                    key={'fold':fi,'target':target,'feature_set':set_name,'model':name}
                    fold_scores.append({**key,**scores(test[target],p)})
                    predictions.extend([{**key,'row_id':row,'probability':float(prob)} for row,prob in zip(test.row_id,p)])
                    if target==TARGETS[0] and name!='dummy':
                        x=test[columns].copy(); x.attrs['dates']=test.decision_time
                        importances.extend(permutation(model,x,test[target],fi,name,set_name))
                        names=model.named_steps['preprocess'].get_feature_names_out()
                        if name=='logistic': coefficients.extend([{**key,'feature':f,'coefficient':float(v)} for f,v in zip(names,model.named_steps['model'].coef_[0])])
                        if name=='forest': impurity.extend([{**key,'feature':f,'importance':float(v)} for f,v in zip(names,model.named_steps['model'].feature_importances_)])
        print('Completed Development fold',fi,fold_info[-1],flush=True)
    save(HERE/'results/fold-audit.json',fold_info); save(HERE/'results/development-fold-metrics.json',fold_scores)
    pd.DataFrame(predictions).to_csv(HERE/'results/development-predictions.csv',index=False)
    pd.DataFrame(importances).to_csv(HERE/'results/block-permutation-importance.csv',index=False)
    pd.DataFrame(coefficients).to_csv(HERE/'results/logistic-coefficients.csv',index=False)
    pd.DataFrame(impurity).to_csv(HERE/'results/forest-impurity-supplement.csv',index=False)
    means=pd.DataFrame(fold_scores).groupby(['target','feature_set','model'])[['roc_auc','pr_auc_ap','balanced_accuracy','precision','recall','f1','brier','ece_5_bins']].mean().reset_index()
    means.to_csv(HERE/'results/development-mean-metrics.csv',index=False)
    candidates=means[(means.target==TARGETS[0])&(means.model!='dummy')].sort_values(['pr_auc_ap','brier'],ascending=[False,True])
    winner=candidates.iloc[0]; freeze={'candidate':winner[['feature_set','model']].to_dict(),'primary_target':TARGETS[0],'primary_threshold':.5,'all_reported_thresholds':THRESHOLDS,'frozen_utc':datetime.now(timezone.utc).isoformat(),'protocol_sha256':sha(HERE/'protocol.json'),'validation_not_loaded_yet':True}
    save(HERE/'frozen-selection.json',freeze)
    # All choices are now locked. No feedback loop from validation to fitting.
    v=load('validation'); validation_scores=[]; economic_rows=[]; val_predictions=[]; pair_scores=[]
    pred=pd.DataFrame(predictions)
    for target in TARGETS:
        for set_name,columns in SETS.items():
            for name in MODELS:
                model=pipeline(name,columns); model.fit(d[columns],d[target]); probabilities=model.predict_proba(v[columns])[:,1]
                key={'target':target,'feature_set':set_name,'model':name}
                validation_scores.append({**key,**scores(v[target],probabilities)})
                val_predictions.extend([{**key,'row_id':row,'probability':float(prob)} for row,prob in zip(v.row_id,probabilities)])
                for pair in ['BTC/USDT','ETH/USDT']:
                    mask=v.pair==pair; pair_scores.append({**key,'pair':pair,**scores(v.loc[mask,target],probabilities[mask])})
                oof=pred[(pred.target==target)&(pred.feature_set==set_name)&(pred.model==name)].merge(d,on='row_id').sort_values(['decision_time','pair'])
                for split,frame,probs in [('development_oof',oof,oof.probability.to_numpy()),('validation',v,probabilities)]:
                    economic_rows.append({**key,'split':split,'threshold':'unfiltered',**economic(frame,np.ones(len(frame),dtype=bool))})
                    for threshold in THRESHOLDS: economic_rows.append({**key,'split':split,'threshold':threshold,**economic(frame,probs>=threshold)})
    save(HERE/'results/validation-metrics.json',validation_scores); save(HERE/'results/validation-pair-metrics.json',pair_scores)
    save(HERE/'results/economics.json',economic_rows); pd.DataFrame(economic_rows).to_csv(HERE/'results/economics.csv',index=False)
    pd.DataFrame(val_predictions).to_csv(HERE/'results/validation-predictions.csv',index=False)
    # Paired calendar-month block bootstrap, only the Development-frozen candidate.
    candidate=pd.DataFrame(val_predictions)
    candidate=candidate[(candidate.target==TARGETS[0])&(candidate.model==freeze['candidate']['model'])&(candidate.feature_set==freeze['candidate']['feature_set'])].merge(v,on='row_id')
    blocks=[g for _,g in candidate.groupby(candidate.decision_time.dt.strftime('%Y-%m'))]
    rng=np.random.default_rng(SEED); samples=[]
    for _ in range(500):
        sample=pd.concat([blocks[i] for i in rng.integers(0,len(blocks),len(blocks))])
        selected=sample.probability>=.5; s=scores(sample[TARGETS[0]],sample.probability)
        samples.append({'roc_auc':s['roc_auc'],'pr_auc_ap':s['pr_auc_ap'],'brier':s['brier'],
                        'profit_delta_vs_unfiltered':float(sample.loc[selected,'net_profit_usdt'].sum()-sample.net_profit_usdt.sum())})
    ci={k:{'low':float(pd.DataFrame(samples)[k].quantile(.025)),'high':float(pd.DataFrame(samples)[k].quantile(.975))} for k in samples[0]}
    save(HERE/'results/candidate-block-bootstrap.json',{'candidate':freeze['candidate'],'method':'500 paired calendar-month block resamples; within-month rows retained; only12 blocks, approximate descriptive uncertainty, cross-month dependence not fully represented','intervals_95pct':ci})
    assert sha(Path(__file__))==protocol['script_sha256'] and sha(HERE/'protocol.json')==freeze['protocol_sha256']
    assert sha(ROOT/'ai_lab/strategies/LabBaseline.py')==expected
    save(HERE/'results/validation_consumed.json',{'status':'complete','candidate':freeze['candidate'],'do_not_retune':True,'finished_utc':datetime.now(timezone.utc).isoformat()})
    print('Complete. Frozen candidate:',freeze['candidate'],flush=True)


if __name__=='__main__': main()

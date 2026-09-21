"""Freeze and fit the user-specified candidate before any shadow access."""
import json
import subprocess
import sys
import joblib
import numpy as np
import pandas as pd
import sklearn
from common import HERE, ROOT, guard, sha, save, log, now, make_pipeline


def main():
    assert not (HERE/'frozen-candidate.json').exists(), 'Freeze already exists; never overwrite'
    branch, strategy_hash = guard()
    protocol = json.loads((ROOT/'ai_lab/ml_models_v2/protocol.json').read_text())
    features = protocol['feature_sets']['B_reduced']
    dataset = ROOT/'ai_lab/ml_dataset_v2/data/A_portfolio.parquet'
    assert sha(dataset) == protocol['source_sha256']
    train = pd.read_parquet(dataset).sort_values(['decision_time','pair'])
    assert len(train)==1271 and train.row_id.is_unique
    assert train.decision_time.min() >= pd.Timestamp('2019-01-01',tz='UTC')
    assert train.decision_time.max() < pd.Timestamp('2025-01-01',tz='UTC')
    assert train.strategy_outcome_end.max() < pd.Timestamp('2025-01-01',tz='UTC')
    assert (train.feature_candle_open+pd.Timedelta(hours=1)<=train.decision_time).all()
    assert not train[features].isna().any().any()
    model = make_pipeline('logistic', features)
    assert model.named_steps['model'].get_params() == protocol['model_parameters']['logistic']
    assert len(features)==36
    inputs = ['ai_lab/ml_models_v2/protocol.json','ai_lab/ml_models_v2/benchmark.py',
              'ai_lab/ml_models_v2/results/predictions.parquet',
              'ai_lab/ml_dataset_v2/schema.json','ai_lab/ml_dataset_v2/feature_builder.py',
              'ai_lab/ml_dataset/features.py','ai_lab/regime/detector.py','ai_lab/regime/specification.json',
              'ai_lab/strategies/LabBaseline.py','ai_lab/configs/backtest.json',
              'ai_lab/ml_dataset_v2/data/A_portfolio.parquet','ai_lab/ml_dataset_v2/build.py',
              'ai_lab/ml_dataset_v2/run_baselines.py','ai_lab/evaluation/protocol.json']
    sources = {name:sha(ROOT/name) for name in inputs}
    sources.update({p.relative_to(ROOT).as_posix():sha(p) for p in HERE.glob('*.py')})
    manifest = {'freeze_utc':now(), 'git_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'git_branch':branch, 'git_status_at_freeze':subprocess.check_output(['git','status','--short'],cwd=ROOT,text=True),
        'choice':'User specified Phase 3C B_reduced LogisticRegression; no selection in Phase 3D',
        'target':'profitable_after_fees', 'threshold':0.55, 'features':features,
        'model_parameters':model.named_steps['model'].get_params(),
        'preprocessing':{'numeric':[c for c in features if c not in ('pair','regime')],
            'scaler':model.named_steps['preprocess'].transformers[0][1].get_params(),
            'categorical':['pair','regime'],
            'encoder':model.named_steps['preprocess'].transformers[1][1].get_params(),
            'fit_scope':'Only the 1271 rows in frozen Dataset A, 2019 through 2024; no calibration refit'},
        'fit_start':'2019-01-01T00:00:00Z','fit_end_exclusive':'2025-01-01T00:00:00Z',
        'fit_rows':len(train), 'training_years':sorted(int(x) for x in train.year.unique()),
        'training_tail':'All actual-strategy outcomes end in 2024. Incomplete forward diagnostic labels are not used.',
        'shadow_start':'2026-04-01T00:00:00Z','shadow_end_exclusive':'2026-09-01T00:00:00Z',
        'warmup':'March 1-April 1 2026, public Binance 1h only; indicator initialization, never fitting or scoring',
        'fee_each_side':0.001,'stake_usdt':100,'wallet_usdt':1000,'max_open_trades':2,
        'attribution':'Actual LabBaseline portfolio entries; features from completed candle immediately preceding entry',
        'labels':'Net profit ratio after existing exchange fees >0. No relabeling or diagnostic horizon optimization.',
        'classification_cutoff':'0.55 primary, with the Phase 3C standard 0.50 classification metrics as a separately labeled compatibility diagnostic; all economics only 0.55',
        'economic_method':'Subset of frozen baseline trades; no newly unlocked entries. Close-time equity with simultaneous closes aggregated; no intratrade equity. This corrects the Phase 3C implementation that used entry-day P/L despite its README saying close-day.',
        'quality_policy':'Require full sealed hourly grid and unchanged hashes. March gaps, if any, are flagged and filled past-close/zero-volume as in Phase 3B. No silent feature imputation; unavailable entry features abort evaluation.',
        'single_shot':'Refuse if started/consumed marker exists. Serialize fitted pipeline before unseal. One predict_proba call; no alternatives.',
        'decision_rules':{
            'A':'AUC>=0.55, AP>=prevalence+0.05, net positive and above baseline, PF>=1.2, >=30 selected, >=10 selected each pair with nonnegative pair profits, all integrity checks pass',
            'B':'If A fails: AUC>0.5 and AP>prevalence, plus filtered net positive and above baseline, all integrity checks pass',
            'C':'Otherwise; failed integrity means no valid evidence, not proof that all ML is ineffective'},
        'shadow_read_in_phase_before_freeze':False, 'strategy_sha256':strategy_hash,
        'source_hashes':sources,'versions':{'python':sys.version,'sklearn':sklearn.__version__,'pandas':pd.__version__}}
    save(HERE/'frozen-candidate.json',manifest)
    log('candidate_frozen',manifest_sha256=sha(HERE/'frozen-candidate.json'),shadow_accessed=False)
    # Stronger ordering than required: finish all fitting before opening any shadow file.
    model.fit(train[features],train[manifest['target']])
    prep = model.named_steps['preprocess']
    numeric = manifest['preprocessing']['numeric']
    np.testing.assert_allclose(prep.named_transformers_['numeric'].mean_,train[numeric].mean().to_numpy(),rtol=1e-12,atol=1e-12)
    assert int(prep.named_transformers_['numeric'].n_samples_seen_)==1271
    joblib.dump(model,HERE/'candidate.joblib')
    save(HERE/'fitted-preprocessing.json',{'fit_rows':1271,'feature_names':prep.get_feature_names_out().tolist(),
        'numeric_means':prep.named_transformers_['numeric'].mean_.tolist(),
        'numeric_scales':prep.named_transformers_['numeric'].scale_.tolist(),
        'categories':[x.tolist() for x in prep.named_transformers_['category'].categories_],
        'coefficient':model.named_steps['model'].coef_.tolist(),'intercept':model.named_steps['model'].intercept_.tolist()})
    guard()
    save(HERE/'pre-unseal-hashes.json',{'utc':now(),'shadow_accessed':False,
        'hashes':{p.name:sha(p) for p in [HERE/'candidate.joblib',HERE/'frozen-candidate.json',HERE/'fitted-preprocessing.json']},
        'source_hashes':sources})
    log('fit_complete_before_unseal',training_rows=1271,training_years=list(range(2019,2025)),
        candidate_sha256=sha(HERE/'candidate.joblib'),shadow_accessed=False,scaler_training_only=True)


if __name__=='__main__': main()

"""Shared immutable Phase 3D paths and audit utilities."""
import os
os.environ.setdefault('OMP_NUM_THREADS', '1')
os.environ.setdefault('OPENBLAS_NUM_THREADS', '1')
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT/'ai_lab/ml_models_v2'))
sys.path.insert(0, str(ROOT/'ai_lab/ml_dataset_v2'))
from benchmark import make_pipeline, metrics
from feature_builder import build_features, NUMERIC, signal_mask


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2, default=str, allow_nan=False)+'\n', encoding='utf-8')


def log(event, **details):
    item = {'utc': now(), 'event': event, **details}
    with (HERE/'audit.jsonl').open('a', encoding='utf-8') as out:
        out.write(json.dumps(item, default=str)+'\n')
    print(json.dumps(item, default=str), flush=True)


def guard():
    branch = subprocess.check_output(['git','branch','--show-current'], cwd=ROOT, text=True).strip()
    assert branch == 'ai-lab-development', branch
    diff = subprocess.check_output(['git','diff','HEAD','--name-only'], cwd=ROOT, text=True)
    assert not diff.strip(), diff
    assert not any(k.startswith('FREQTRADE__') for k in os.environ)
    expected = json.loads((ROOT/'ai_lab/evaluation/protocol.json').read_text())['strategy_sha256']
    assert sha(ROOT/'ai_lab/strategies/LabBaseline.py') == expected
    return branch, expected


def economics(d):
    import numpy as np
    trades = d.sort_values(['strategy_outcome_end','pair'])
    p = trades.net_profit_usdt
    gains = float(p[p>0].sum()); losses = float(-p[p<0].sum())
    equity = np.r_[1000., 1000+trades.groupby('strategy_outcome_end').net_profit_usdt.sum().sort_index().cumsum().to_numpy()]
    peaks = np.maximum.accumulate(equity)
    streak = longest = 0
    for value in p:
        streak = streak+1 if value < 0 else 0
        longest = max(longest, streak)
    return {'trades':len(d), 'wins':int((p>0).sum()), 'losses':int((p<0).sum()),
            'win_rate_pct':float((p>0).mean()*100) if len(d) else None,
            'net_usdt':float(p.sum()), 'return_on_1000_pct':float(p.sum()/10),
            'average_trade_pct':float(d.net_profit_ratio.mean()*100) if len(d) else None,
            'profit_factor':gains/losses if losses else None,
            'profit_factor_note':'no losing trades' if not losses and gains else 'no trades' if not len(d) else None,
            'expectancy_usdt':float(p.mean()) if len(d) else None,
            'closed_trade_max_drawdown_pct':float(((peaks-equity)/peaks).max()*100),
            'consecutive_losses':longest,
            'regime_counts':{str(k):int(v) for k,v in d.regime.value_counts().items()},
            'average_duration_minutes':float(d.duration_minutes.mean()) if len(d) else None}


def classification(y, probabilities):
    from sklearn.metrics import balanced_accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
    import numpy as np
    result=metrics(y,probabilities)
    result['phase3c_standard_cutoff_0_50']={k:result[k] for k in ['balanced_accuracy','precision','recall','f1','confusion_matrix']}
    selected=np.asarray(probabilities)>=.55
    result.update({'decision_threshold':.55,
        'balanced_accuracy':float(balanced_accuracy_score(y,selected)),
        'precision':float(precision_score(y,selected,zero_division=0)),
        'recall':float(recall_score(y,selected,zero_division=0)),
        'f1':float(f1_score(y,selected,zero_division=0)),
        'confusion_matrix':confusion_matrix(y,selected,labels=[0,1]).tolist()})
    return result

"""Recover a pre-prediction timestamp precision assertion, preserving frozen files."""
import json
import hashlib
from common import HERE, sha, save, log, now


def record_resume(value):
    # Keep the original start timestamp; never erase or replace the original marker.
    log('technical_resume_start',original_start=json.loads((HERE/'EVALUATION_STARTED.json').read_text()),
        manifest_sha256=value['manifest_sha256'])


def main():
    assert (HERE/'EVALUATION_STARTED.json').exists()
    assert not (HERE/'CONSUMED.json').exists()
    assert not (HERE/'shadow-predictions.parquet').exists()
    assert not (HERE/'backtest').exists() or not list((HERE/'backtest').glob('*.zip'))
    events=[json.loads(line) for line in (HERE/'audit.jsonl').read_text().splitlines()]
    assert not any(e['event']=='single_prediction_call' for e in events)
    assert events[-1]['event']=='evaluation_error' and events[-1]['type']=='AssertionError'
    path=HERE/'evaluate.py'
    original=path.read_text(encoding='utf-8')
    changes={
        "assert not (HERE/'EVALUATION_STARTED.json').exists(), 'Single-shot evaluation already started; no automatic rerun'":
        "assert (HERE/'EVALUATION_STARTED.json').exists(), 'Recovery requires original start marker'",
        "save(HERE/'EVALUATION_STARTED.json',": "record_resume(",
        "assert pd.DatetimeIndex(prices.date).equals(grid)":
        "assert len(prices)==len(grid) and bool((pd.DatetimeIndex(prices.date)==grid).all()), 'Hourly timestamp values differ'",
    }
    corrected=original
    for before,after in changes.items():
        assert corrected.count(before)==1,before
        corrected=corrected.replace(before,after)
    save(HERE/'timestamp-recovery.json',{'utc':now(),'reason':'Same timestamps stored as datetime64[ms] versus datetime64[us]; Index.equals is dtype-sensitive.',
        'before_recovery_predictions':0,'before_recovery_baseline_runs':0,'candidate_changes':[],
        'frozen_evaluate_file_preserved_sha256':sha(path),'recovery_script_sha256':sha(HERE/'resume_timestamp_check.py'),
        'effective_code_sha256':hashlib.sha256(corrected.encode()).hexdigest(),'exact_replacements':changes})
    log('timestamp_precision_recovery',candidate_unchanged=True,previous_predictions=0)
    env={'__name__':'phase3d_recovery','__file__':str(path),'record_resume':record_resume}
    exec(compile(corrected,str(path),'exec'),env)
    try: env['main']()
    except Exception as error:
        log('evaluation_error',type=type(error).__name__,message=str(error))
        raise


if __name__=='__main__': main()

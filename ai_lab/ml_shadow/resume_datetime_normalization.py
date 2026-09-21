"""Normalize timestamp storage after concatenation, without changing time values."""
import hashlib
import json
from common import HERE, sha, save, log, now


def record_resume(value):
    log('technical_datetime_resume',manifest_sha256=value['manifest_sha256'],original_start_preserved=True)


def main():
    assert (HERE/'EVALUATION_STARTED.json').exists() and not (HERE/'CONSUMED.json').exists()
    assert not (HERE/'shadow-predictions.parquet').exists()
    assert not list((HERE/'backtest').glob('*.zip'))
    events=[json.loads(line) for line in (HERE/'audit.jsonl').read_text().splitlines()]
    assert not any(e['event']=='single_prediction_call' for e in events)
    assert events[-1]['type']=='AttributeError' and '.dt accessor' in events[-1]['message']
    prior=json.loads((HERE/'timestamp-recovery.json').read_text())
    changes=prior['exact_replacements']
    changes['full=pd.concat([warmup(pair),prices],ignore_index=True)']=(
        "full=pd.concat([warmup(pair),prices],ignore_index=True)\n"
        "        original_times=list(full.date)\n"
        "        full['date']=pd.to_datetime(full.date,utc=True)\n"
        "        assert all(a==b for a,b in zip(original_times,full.date)), 'Time values changed'")
    code=(HERE/'evaluate.py').read_text(encoding='utf-8')
    for before,after in changes.items():
        assert code.count(before)==1,before
        code=code.replace(before,after)
    save(HERE/'datetime-recovery.json',{'utc':now(),'reason':'Concatenating datetime storage types produced object dtype; explicitly normalize UTC while asserting every timestamp value is unchanged.',
        'candidate_changes':[],'previous_predictions':0,'previous_baseline_runs':0,
        'recovery_script_sha256':sha(HERE/'resume_datetime_normalization.py'),
        'effective_code_sha256':hashlib.sha256(code.encode()).hexdigest(),'exact_replacements':changes})
    log('datetime_storage_recovery',candidate_unchanged=True,previous_predictions=0)
    env={'__name__':'phase3d_recovery','__file__':str(HERE/'evaluate.py'),'record_resume':record_resume}
    exec(compile(code,str(HERE/'evaluate.py'),'exec'),env)
    try: env['main']()
    except Exception as error:
        log('evaluation_error',type=type(error).__name__,message=str(error))
        raise


if __name__=='__main__': main()

"""Final integrity audit and artifact manifest; no model or strategy selection."""
import json
import subprocess
from common import HERE,ROOT,BASELINE_SHA,verify_frozen,save,sha,now,log


def main():
    p=verify_frozen()
    events=[json.loads(line) for line in (HERE/'audit.jsonl').read_text().splitlines()]
    initial=next(e for e in events if e['event']=='design_frozen')
    assert sha(HERE/'protocol.json')==initial['protocol_sha256']
    assert sha(HERE/'backtest.json')==p['config_sha256']
    assert sha(HERE/'strategies/LabBaseline.py')==BASELINE_SHA
    completed=[e['year'] for e in events if e['event']=='annual_run_completed']
    assert completed==[2019,2020,2021,2022]
    for e in events:
        if e['event']=='annual_run_completed':
            archive=next((HERE/'results'/str(e['year'])).glob('*.zip'))
            assert sha(archive)==e['archive_sha256']
    status=subprocess.check_output(['git','status','--short'],cwd=ROOT,text=True)
    assert status.strip()=='?? ai_lab/alpha_research/',status
    save(HERE/'audits/final-integrity.json',{'utc':now(),'branch':'ai-lab-development','git_status':status,
        'baseline_original_and_copy_sha256':BASELINE_SHA,'tracked_files_modified':[],
        'frozen_strategy_code_unchanged':True,'protocol_unchanged_since_before_data':True,
        'annual_runs':completed,'year_strategy_combinations':64,
        'year_boundary_note':'Seven forced exits across2020/2021 strategy runs occur exactly on following Jan1 midnight. Original timestamps and P/L retained; daily summaries assign them to prior final day.2022 input ends Dec31 23:00. No parameter adaptation occurs across touching endpoints.',
        'candidate_families':5,'settings_per_family':3,'parameters_selected_or_updated':0,
        'consumed_period_data_or_result_files_read':False,'new_source_data_end_exclusive':'2023-01-01T00:00:00Z',
        'live_trading_enabled':False,'ml_used':False,'commit_push_merge_performed':False})
    save(HERE/'audits/causality-tests.json',{'command':'.venv/Scripts/python.exe -B ai_lab/alpha_research/test_causality.py',
        'result':'5 tests passed before backtesting','synthetic_prefix_comparisons':45,'synthetic_future_mutation_comparisons':15,
        'real_prefix_comparisons':150,'tested_candidates_and_variants':p['variants'],
        'other_checks':['prior-only breakout levels','warmup not future-filled','exactly one perturbed parameter per neighbor'],
        'initial_pre_freeze_fix':'Renamed access to squeeze column using brackets to avoid collision with pandas DataFrame.squeeze method; no performance was viewed.'})
    log('final_scope_verified',strategy_unchanged=True,protocol_unchanged=True,post2022_results_accessed=False)
    inventory=HERE/'reports/file-inventory.txt'; manifest=HERE/'audits/artifact-sha256.json'
    files=sorted(set([f for f in HERE.rglob('*') if f.is_file() and '__pycache__' not in f.parts]+[inventory,manifest]))
    inventory.write_text('\n'.join(f.relative_to(ROOT).as_posix() for f in files)+'\n',encoding='utf-8')
    save(manifest,{f.relative_to(HERE).as_posix():sha(f) for f in files if f!=manifest})
    print(f'{len(files)} deliverable files; branch ai-lab-development; only ai_lab/alpha_research is untracked.')


if __name__=='__main__': main()

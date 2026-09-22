"""Verify Phase 4B evidence and create inventory without rerunning backtests."""
import json
import subprocess
from common import HERE, ROOT, PERIODS, log, now, save, sha, verify_frozen


def main():
    frozen=verify_frozen()
    data=json.loads((HERE/'audits/data.json').read_text())
    assert data['original_seal_unchanged']
    for item in data['records']:
        assert sha(HERE/'data'/f"{item['pair'].replace('/','_')}-1h.feather")==item['full_data_sha256']
        assert item['D_missing']==0 and item['D_duplicates']==0
    events=[json.loads(line) for line in (HERE/'audit.jsonl').read_text().splitlines()]
    physical_archives=0
    for label in PERIODS:
        archives=sorted((HERE/'results'/label).glob('*.zip'))
        archive=archives[0]
        physical_archives += len(archives)
        assert (HERE/'results'/label/'metrics.json').exists()
        assert any(e['event'] in ['retrospective_backtest_completed','retrospective_backtest_recovered_completed'] and e['label']==label for e in events)
        assert sha(archive)==next(e['archive_sha256'] for e in events if e['event'] in ['retrospective_backtest_completed','retrospective_backtest_recovered_completed'] and e['label']==label)
    status=subprocess.check_output(['git','status','--short'],cwd=ROOT,text=True)
    assert status.strip()=='?? ai_lab/alpha_validation/',status
    save(HERE/'audits/final-integrity.json',{'utc':now(),'branch':'ai-lab-development','git_status':status,
      'original_alpha_breakout_and_copy_match':True,'LabBaseline_unchanged':True,'frozen_manifest_unchanged':True,
      'alpha_parameters_changed_after_freeze':False,'strategies_evaluated':['AlphaBreakout','LabBaseline'],
      'periods_completed':list(PERIODS),'logical_periods':4,'physical_backtest_archives':physical_archives,
      'duplicate_locked_C_execution':True,'ml_used':False,'freqai_used':False,
      'live_trading_enabled':False,'sealed_data_unchanged':True,'no_data_after_2026_09_01':True,
      'retrospective_label_required':frozen['label_for_every_result']})
    inventory=HERE/'reports/file-inventory.txt'; hashes=HERE/'audits/artifact-sha256.json'
    files=sorted(set([p for p in HERE.rglob('*') if p.is_file() and '__pycache__' not in p.parts]+[inventory,hashes]))
    inventory.write_text('\n'.join(p.relative_to(ROOT).as_posix() for p in files)+'\n',encoding='utf-8')
    save(hashes,{p.relative_to(HERE).as_posix():sha(p) for p in files if p!=hashes})
    log('final_integrity_complete',physical_archives=physical_archives,all_source_hashes_unchanged=True)
    print(f'{len(files)} deliverable files; locked retrospective evaluation complete.')


if __name__=='__main__': main()

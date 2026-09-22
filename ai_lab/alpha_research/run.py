"""Four annual Freqtrade runs; all declared hypotheses/perturbations, no search."""
import json
import os
import subprocess
import sys
import zipfile
from common import HERE,ROOT,VARIANTS,verify_frozen,save,sha,log


def main():
    p=verify_frozen()
    assert sha(HERE/'backtest.json')==p['config_sha256']
    assert not any(k.startswith('FREQTRADE__') for k in os.environ)
    data=json.loads((HERE/'audits/data.json').read_text())
    for rec in data:
        assert sha(HERE/'data'/f"{rec['pair'].replace('/','_')}-1h.feather")==rec['engine_sha256']
    for year in [2019,2020,2021,2022]:
        output=HERE/'results'/str(year); output.mkdir(exist_ok=True)
        assert not list(output.glob('*.zip')),'Preserve existing annual evidence'
        cmd=[sys.executable,'-B','-m','freqtrade','backtesting','--config',str(HERE/'backtest.json'),
            '--userdir',str(HERE),'--datadir',str(HERE/'data'),'--strategy-path',str(HERE/'strategies'),
            '--strategy-list','LabBaseline',*VARIANTS,'--timerange',f'{year}0101-{year+1}0101',
            '--fee','0.001','--cache','none','--export','trades','--backtest-directory',str(output)]
        save(output/'command.json',cmd); log('annual_run_started',year=year,strategies=16,command=cmd)
        with (output/'output.log').open('w',encoding='utf-8') as out:
            subprocess.run(cmd,cwd=ROOT,stdout=out,stderr=subprocess.STDOUT,check=True,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
        archive=next(output.glob('*.zip'))
        with zipfile.ZipFile(archive) as z:
            name=next(n for n in z.namelist() if n.endswith('.json') and not n.endswith('_config.json'))
            result=json.loads(z.read(name))
        assert set(result['strategy'])==set(['LabBaseline',*VARIANTS])
        save(output/'metrics.json',result['strategy'])
        verify_frozen()
        log('annual_run_completed',year=year,archive_sha256=sha(archive))


if __name__=='__main__': main()

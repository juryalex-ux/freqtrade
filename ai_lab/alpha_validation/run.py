"""Run only frozen AlphaBreakout and permanent LabBaseline for all four periods."""
import json
import os
import subprocess
import sys
import zipfile
from common import HERE, PERIODS, log, save, sha, verify_frozen


def main():
    frozen=verify_frozen()
    assert sha(HERE/'backtest.json')==frozen['validation_source_hashes']['backtest.json']
    data=json.loads((HERE/'audits/data.json').read_text())
    for item in data['records']:
        assert sha(HERE/'data'/f"{item['pair'].replace('/','_')}-1h.feather")==item['full_data_sha256']
    assert not any(key.startswith('FREQTRADE__') for key in os.environ)
    for label,(start,end) in PERIODS.items():
        output=HERE/'results'/label; output.mkdir(exist_ok=True)
        existing=list(output.glob('*.zip'))
        if existing:
            # Recovery after an interrupted multi-period runner: retain the
            # finished evidence byte-for-byte and move to the next period.
            assert len(existing)==1 and (output/'metrics.json').exists()
            log('retrospective_backtest_recovered_completed',label=label,archive_sha256=sha(existing[0]),rerun=False)
            continue
        command=[sys.executable,'-B','-m','freqtrade','backtesting','--config',str(HERE/'backtest.json'),
            '--userdir',str(HERE),'--datadir',str(HERE/'data'),'--strategy-path',str(HERE/'strategies'),
            '--strategy-list','AlphaBreakout','LabBaseline','--timerange',f'{start}-{end}','--fee','0.001',
            '--cache','none','--export','trades','--backtest-directory',str(output)]
        save(output/'command.json',command)
        log('retrospective_backtest_started',label=label,period=[start,end],strategies=['AlphaBreakout','LabBaseline'])
        with (output/'output.log').open('w',encoding='utf-8') as file:
            subprocess.run(command,cwd=HERE.parents[1],stdout=file,stderr=subprocess.STDOUT,check=True,
                           env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
        archive=next(output.glob('*.zip'))
        with zipfile.ZipFile(archive) as z:
            name=next(n for n in z.namelist() if n.endswith('.json') and not n.endswith('_config.json'))
            result=json.loads(z.read(name))['strategy']
        assert set(result)=={'AlphaBreakout','LabBaseline'}
        save(output/'metrics.json',result)
        verify_frozen()
        log('retrospective_backtest_completed',label=label,archive_sha256=sha(archive))


if __name__=='__main__': main()

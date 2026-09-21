"""Same strategy engine for portfolio and unrestricted independent signal entries."""
import hashlib,json,os,subprocess,sys,zipfile
from pathlib import Path
HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[1]


def main():
    assert subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()=='ai-lab-development'
    assert not any(k.startswith('FREQTRADE__') for k in os.environ)
    expected=json.loads((ROOT/'ai_lab/evaluation/protocol.json').read_text())['strategy_sha256']
    assert hashlib.sha256((ROOT/'ai_lab/strategies/LabBaseline.py').read_bytes()).hexdigest()==expected
    for name in ['portfolio','opportunities']:
        output=HERE/'results'/name; output.mkdir(exist_ok=True)
        assert not list(output.glob('*.zip')), 'Do not overwrite completed baseline evidence'
        cmd=[sys.executable,'-B','-m','freqtrade','backtesting','--config','ai_lab/configs/backtest.json','--userdir',str(HERE),
             '--datadir',str(HERE/'engine_data'),'--strategy','LabBaseline','--strategy-path','ai_lab/strategies',
             '--timerange','20190101-20250101','--fee','0.001','--cache','none','--export','trades','--backtest-directory',str(output)]
        if name=='opportunities': cmd+=['--enable-position-stacking','--max-open-trades','-1','--dry-run-wallet','1000000000']
        (output/'command.json').write_text(json.dumps(cmd,indent=2))
        print('Running',name,flush=True)
        with (output/'output.log').open('w') as log:
            subprocess.run(cmd,cwd=ROOT,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),stdout=log,stderr=subprocess.STDOUT,check=True)
        with zipfile.ZipFile(next(output.glob('*.zip'))) as z:
            file=next(n for n in z.namelist() if n.endswith('.json') and not n.endswith('_config.json'))
            metrics=json.loads(z.read(file))['strategy']['LabBaseline']
        (output/'metrics.json').write_text(json.dumps(metrics,indent=2))
        print(name,metrics['total_trades'],'trades; rejected',metrics['rejected_signals'],flush=True)
    assert hashlib.sha256((ROOT/'ai_lab/strategies/LabBaseline.py').read_bytes()).hexdigest()==expected


if __name__=='__main__': main()

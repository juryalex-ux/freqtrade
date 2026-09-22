"""Phase 4A scope and audit utilities. Never imports consumed-period analyses."""
import hashlib
import json
from pathlib import Path
import subprocess
from datetime import datetime,timezone

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
BASELINE_SHA='e7e32ae09ae5f6584afad52428f0f648e4f33dd92f352b6d04b763ad2c2e234c'
CENTRAL=['AlphaTrend','AlphaBreakout','AlphaReversion','AlphaSqueeze','AlphaMomentum']
VARIANTS=[x+s for x in CENTRAL for s in ['', 'Lo','Hi']]


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def now(): return datetime.now(timezone.utc).isoformat()
def save(p,obj): p.write_text(json.dumps(obj,indent=2,default=str,allow_nan=False)+'\n',encoding='utf-8')


def log(event,**data):
    record={'utc':now(),'event':event,**data}
    with (HERE/'audit.jsonl').open('a',encoding='utf-8') as out: out.write(json.dumps(record,default=str)+'\n')
    print(json.dumps(record,default=str),flush=True)


def guard():
    assert subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()=='ai-lab-development'
    changed=subprocess.check_output(['git','diff','HEAD','--name-only'],cwd=ROOT,text=True)
    assert not changed.strip(),changed
    assert sha(ROOT/'ai_lab/strategies/LabBaseline.py')==BASELINE_SHA


def verify_frozen():
    guard()
    frozen=json.loads((HERE/'protocol.json').read_text())
    for name,digest in frozen['code_hashes'].items(): assert sha(HERE/name)==digest,name
    return frozen

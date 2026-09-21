"""Download and seal shadow prices; never import strategy or regime detector."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone
import pandas as pd

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]


def main():
    assert subprocess.check_output(["git","branch","--show-current"],cwd=ROOT,text=True).strip()=="ai-lab-development"
    assert not any(k.startswith("FREQTRADE__") for k in os.environ)
    seal=HERE/"shadow/SEALED.json"
    assert not seal.exists(), "Already sealed; no overwrite"
    cmd=[sys.executable,"-B","-m","freqtrade","download-data","--config","ai_lab/configs/backtest.json",
         "--userdir",str(HERE),"--datadir",str(HERE/"shadow/data"),"--pairs","BTC/USDT","ETH/USDT",
         "--timeframes","1h","--timerange","20260401-20260901"]
    with (HERE/"shadow/download.log").open("w") as log:
        subprocess.run(cmd,cwd=ROOT,env=dict(os.environ,PYTHONDONTWRITEBYTECODE="1"),stdout=log,stderr=subprocess.STDOUT,check=True)
    records=[]
    grid=pd.date_range("2026-04-01","2026-09-01",freq="h",inclusive="left",tz="UTC")
    for pair in ["BTC/USDT","ETH/USDT"]:
        f=HERE/"shadow/data"/(pair.replace("/","_")+"-1h.feather")
        d=pd.read_feather(f)
        # Timestamp-only integrity checks; no price statistics, labels or performance.
        d=d[(d.date>=grid[0]) & (d.date<pd.Timestamp("2026-09-01",tz="UTC"))].reset_index(drop=True)
        assert not d.date.duplicated().any() and d.date.is_monotonic_increasing
        missing=grid.difference(pd.DatetimeIndex(d.date))
        assert not len(missing), "Shadow data incomplete; do not claim sealed"
        d.to_feather(f)
        records.append({"pair":pair,"file":str(f.relative_to(HERE)),"candles":len(d),"sha256":hashlib.sha256(f.read_bytes()).hexdigest(),"missing":0,"duplicates":0})
    seal.write_text(json.dumps({"status":"SEALED_UNEVALUATED","start_utc":"2026-04-01T00:00:00Z","end_exclusive_utc":"2026-09-01T00:00:00Z",
                               "sealed_utc":datetime.now(timezone.utc).isoformat(),"files":records,"download_command":cmd,
                               "rules":"No detector, strategy, performance or threshold selection applied. Future unsealing requires a separately approved protocol.",
                               "provenance_limit":"Earlier end-bounded downloads may have cached boundary candles; no shadow-window strategy or regime evaluation was performed here."},indent=2)+"\n")
    print(seal.read_text())


if __name__=="__main__": main()

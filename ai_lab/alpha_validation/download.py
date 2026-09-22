"""Fetch A-C and append existing sealed D; audit without modifying sealed files."""
import json
import time
import numpy as np
import pandas as pd
import requests
from common import HERE, ROOT, log, save, sha, verify_frozen

START = pd.Timestamp('2022-12-01', tz='UTC')
D_START = pd.Timestamp('2026-04-01', tz='UTC')
END = pd.Timestamp('2026-09-01', tz='UTC')


def main():
    frozen = verify_frozen()
    assert not list((HERE/'data').glob('*-1h.feather')), 'Data exists; do not overwrite.'
    seal = json.loads((ROOT/'ai_lab/regime/shadow/SEALED.json').read_text())
    original_seal_hash = sha(ROOT/'ai_lab/regime/shadow/SEALED.json')
    session = requests.Session(); audits = []; annual = []
    for pair in frozen['pairs']:
        def fetch(start_ms, end_ms):
            args = {'symbol': pair.replace('/',''), 'interval': '1h', 'startTime': start_ms, 'endTime': end_ms, 'limit': 1000}
            for attempt in range(4):
                try:
                    response = session.get('https://api.binance.com/api/v3/klines', params=args, timeout=45)
                    response.raise_for_status(); values = response.json(); assert isinstance(values, list)
                    return values
                except (requests.RequestException, AssertionError):
                    if attempt == 3: raise
                    time.sleep(2)
        rows=[]; cursor=int(START.timestamp()*1000); stop=int(D_START.timestamp()*1000)-1
        while cursor <= stop:
            batch=fetch(cursor,stop)
            if not batch: break
            rows.extend(batch); cursor=int(batch[-1][0])+3600000
        raw=pd.DataFrame([[r[0],*map(float,r[1:6])] for r in rows],columns=['date','open','high','low','close','volume'])
        raw.date=pd.to_datetime(raw.date,unit='ms',utc=True)
        assert raw.date.is_unique and raw.date.is_monotonic_increasing and raw.date.min()==START and raw.date.max()<D_START
        grid=pd.date_range(START,D_START,freq='h',inclusive='left')
        missing=grid.difference(pd.DatetimeIndex(raw.date)); groups=[]
        for stamp in missing:
            if groups and stamp==groups[-1][-1]+pd.Timedelta(hours=1): groups[-1].append(stamp)
            else: groups.append([stamp])
        for group in groups:
            assert len(group)<=12, 'Long gap: stop rather than fabricate.'
            assert not fetch(int(group[0].timestamp()*1000),int((group[-1]+pd.Timedelta(hours=1)).timestamp()*1000)-1), 'Recoverable gap: stop.'
        assert raw.notna().all().all() and (raw.low>0).all() and (raw.volume>=0).all()
        raw.to_feather(HERE/'raw'/f"{pair.replace('/','_')}-preD-raw.feather")
        # Preserve the observed file, while using the existing lab's explicit
        # previous-close/zero-volume policy for confirmed short exchange gaps.
        pre_grid=pd.date_range(START,D_START,freq='h',inclusive='left')
        filled=raw.set_index('date').reindex(pre_grid)
        filled['synthetic']=filled.close.isna()
        prior=filled.close.ffill()
        for column in ['open','high','low','close']:
            filled[column]=filled[column].fillna(prior)
        filled['volume']=filled.volume.fillna(0.)
        assert not filled[['open','high','low','close','volume']].isna().any().any()
        filled=filled.reset_index(names='date')
        record=next(x for x in seal['files'] if x['pair']==pair)
        sealed=(ROOT/'ai_lab/regime'/record['file']).resolve()
        assert sha(sealed)==record['sha256'], 'Sealed data hash mismatch.'
        d=pd.read_feather(sealed)
        d['date']=pd.to_datetime(d.date,utc=True)
        shadow_grid=pd.date_range(D_START,END,freq='h',inclusive='left')
        assert len(d)==record['candles'] and bool((pd.DatetimeIndex(d.date)==shadow_grid).all())
        d['synthetic']=False
        combined=pd.concat([filled,d],ignore_index=True)
        combined['date']=pd.to_datetime(combined.date,utc=True)
        full_grid=pd.date_range(START,END,freq='h',inclusive='left')
        assert len(combined)==len(full_grid) and combined.date.is_unique and bool((pd.DatetimeIndex(combined.date)==full_grid).all())
        combined.to_feather(HERE/'data'/f"{pair.replace('/','_')}-1h.feather")
        for year, group in combined.groupby(combined.date.dt.year):
            annual.append({'pair':pair,'year':int(year),'candles':len(group),'synthetic':0})
        audits.append({'pair':pair,'preD_raw_sha256':sha(HERE/'raw'/f"{pair.replace('/','_')}-preD-raw.feather"),
                       'full_data_sha256':sha(HERE/'data'/f"{pair.replace('/','_')}-1h.feather"),
                       'sealed_D_file':record['file'],'sealed_D_sha256':record['sha256'],
                       'preD_start':str(raw.date.min()),'preD_end':str(raw.date.max()),
                       'preD_missing':len(missing),'preD_missing_timestamps':list(map(str,missing)),
                       'preD_gap_lengths':[len(x) for x in groups],'preD_synthetic':int(filled.synthetic.sum()),'D_missing':0,'D_duplicates':0,
                       'post_shadow_data':0})
        log('data_ready',pair=pair,preD_observed=len(raw),D_sealed_candles=len(d),preD_missing=len(missing))
    assert sha(ROOT/'ai_lab/regime/shadow/SEALED.json')==original_seal_hash
    save(HERE/'audits/data.json',{'records':audits,'original_seal_sha256':original_seal_hash,'original_seal_unchanged':True})
    pd.DataFrame(annual).to_csv(HERE/'reports/candle-counts.csv',index=False)


if __name__=='__main__': main()

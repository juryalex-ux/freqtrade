"""Download bounded pre-2025 Binance spot OHLCV; audit rather than hide gaps."""
import hashlib,json,time,subprocess
from pathlib import Path
import requests
import pandas as pd

HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[1]
START=pd.Timestamp('2018-12-01',tz='UTC'); END=pd.Timestamp('2025-01-01',tz='UTC')
URL='https://api.binance.com/api/v3/klines'


def main():
    assert subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()=='ai-lab-development'
    session=requests.Session(); audits={}; counts=[]; anomalies=[]
    for symbol in ['BTCUSDT','ETHUSDT']:
        rows=[]; cursor=int(START.timestamp()*1000); stop=int(END.timestamp()*1000)-1
        def request(start,end,limit=1000):
            for attempt in range(5):
                try:
                    r=session.get(URL,params={'symbol':symbol,'interval':'1h','startTime':start,'endTime':end,'limit':limit},timeout=30)
                    r.raise_for_status(); result=r.json(); assert isinstance(result,list)
                    return result
                except (requests.RequestException,AssertionError):
                    if attempt==4: raise
                    time.sleep(2**attempt)
        while cursor<=stop:
            batch=request(cursor,stop)
            if not batch: break
            rows.extend(batch); cursor=batch[-1][0]+3600000
            if len(rows)%10000==0: print(symbol,len(rows),flush=True)
        raw=pd.DataFrame([[r[0],*map(float,r[1:6])] for r in rows],columns=['date','open','high','low','close','volume'])
        raw.date=pd.to_datetime(raw.date,unit='ms',utc=True)
        assert not raw.date.duplicated().any() and raw.date.is_monotonic_increasing
        assert (raw.date<END).all() and raw.date.min()==START
        expected=pd.date_range(START,END,freq='h',inclusive='left'); missing=expected.difference(pd.DatetimeIndex(raw.date))
        groups=[]
        for timestamp in missing:
            if groups and timestamp==groups[-1][-1]+pd.Timedelta(hours=1): groups[-1].append(timestamp)
            else: groups.append([timestamp])
        for group in groups:
            # Independently re-request precisely the gap. No synthetic bars are hidden.
            check=request(int(group[0].timestamp()*1000),int((group[-1]+pd.Timedelta(hours=1)).timestamp()*1000)-1)
            assert not check, f'Transient download gap {symbol} {group}; rerun download'
            assert len(group)<=12, 'Long outage requires explicit review, not silent filling'
        assert raw[['open','high','low','close','volume']].notna().all().all()
        assert ((raw.low<=raw[['open','close']].min(axis=1))&(raw.high>=raw[['open','close']].max(axis=1))&(raw.volume>=0)&(raw.low>0)).all()
        filename=symbol.replace('USDT','_USDT')+'-1h.feather'; raw.to_feather(HERE/'raw'/filename)
        filled=raw.set_index('date').reindex(expected); filled['synthetic']=filled.close.isna()
        previous=filled.close.ffill()
        for c in ['open','high','low','close']: filled[c]=filled[c].fillna(previous)
        filled.volume=filled.volume.fillna(0); filled.index.name='date'; filled=filled.reset_index()
        filled.to_feather(HERE/'data'/filename)
        filled[['date','open','high','low','close','volume']].to_feather(HERE/'engine_data'/filename)
        for year,g in filled[filled.date>=pd.Timestamp('2019-01-01',tz='UTC')].groupby(filled.date.dt.year):
            counts.append({'pair':symbol,'year':int(year),'expected':len(g),'observed':int((~g.synthetic).sum()),'synthetic':int(g.synthetic.sum()),'observed_zero_volume':int(((g.volume==0)&(~g.synthetic)).sum())})
        returns=raw.close.pct_change(fill_method=None); gaps=raw.open/raw.close.shift(1)-1
        flagged=raw[(returns.abs()>.10)|(gaps.abs()>.02)].copy()
        for i,r in flagged.iterrows(): anomalies.append({'pair':symbol,'date':str(r.date),'hourly_close_return':float(returns.loc[i]),'open_previous_close_gap':float(gaps.loc[i])})
        audits[symbol]={'start':str(raw.date.min()),'end':str(raw.date.max()),'raw_count':len(raw),'duplicates':0,'ordered':True,'missing_utc':list(map(str,missing)),
                        'verified_gap_lengths':[len(g) for g in groups],'zero_volume_raw':int((raw.volume==0).sum()),'discontinuity_flags':len(flagged),
                        'raw_sha256':hashlib.sha256((HERE/'raw'/filename).read_bytes()).hexdigest(),'policy':'All missing timestamps re-requested and confirmed absent. Explicit previous-close/zero-volume fill with synthetic flag; no long unavailable history fabricated.'}
        print(symbol,'complete',len(raw),'missing',len(missing),flush=True)
    (HERE/'audits/candles.json').write_text(json.dumps(audits,indent=2)+'\n')
    pd.DataFrame(counts).to_csv(HERE/'reports/candles-by-year.csv',index=False)
    pd.DataFrame(anomalies).to_csv(HERE/'audits/discontinuities.csv',index=False)


if __name__=='__main__': main()

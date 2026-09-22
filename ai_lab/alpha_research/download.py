"""New end-bounded public candles; never opens mixed/consumed-period datasets."""
import time
import pandas as pd
import requests
from common import HERE,verify_frozen,save,sha,log


def main():
    p=verify_frozen(); start=pd.Timestamp(p['data_start'],tz='UTC'); end=pd.Timestamp(p['data_end_exclusive'],tz='UTC')
    assert end==pd.Timestamp('2023-01-01',tz='UTC')
    grid=pd.date_range(start,end,freq='h',inclusive='left'); audits=[]; counts=[]
    session=requests.Session()
    for pair in p['execution']['pairs']:
        path=HERE/'raw'/f"{pair.replace('/','_')}-1h.feather"
        assert not path.exists(),'Raw data already exists; do not overwrite'
        def fetch(a,b):
            args={'symbol':pair.replace('/',''),'interval':'1h','startTime':a,'endTime':b,'limit':1000}
            for attempt in range(4):
                try:
                    response=session.get('https://api.binance.com/api/v3/klines',params=args,timeout=30)
                    response.raise_for_status(); values=response.json(); assert isinstance(values,list)
                    return values
                except (requests.RequestException,AssertionError):
                    if attempt==3: raise
                    time.sleep(2)
        rows=[]; cursor=int(start.timestamp()*1000); stop=int(end.timestamp()*1000)-1
        while cursor<=stop:
            values=fetch(cursor,stop)
            if not values: break
            rows.extend(values); cursor=int(values[-1][0])+3600000
            if len(rows)%10000==0: log('download_progress',pair=pair,rows=len(rows),last_timestamp_ms=int(values[-1][0]))
        raw=pd.DataFrame([[r[0],*map(float,r[1:6])] for r in rows],columns=['date','open','high','low','close','volume'])
        raw['date']=pd.to_datetime(raw.date,unit='ms',utc=True)
        assert raw.date.is_unique and raw.date.is_monotonic_increasing and raw.date.min()==start and raw.date.max()<end
        assert raw.notna().all().all()
        missing=grid.difference(pd.DatetimeIndex(raw.date)); groups=[]
        for stamp in missing:
            if groups and stamp==groups[-1][-1]+pd.Timedelta(hours=1): groups[-1].append(stamp)
            else: groups.append([stamp])
        for group in groups:
            assert len(group)<=12,'Long missing history: stop'
            assert not fetch(int(group[0].timestamp()*1000),int((group[-1]+pd.Timedelta(hours=1)).timestamp()*1000)-1),'Recoverable gap; stop for transparent repair'
        assert (raw.low>0).all() and (raw.volume>=0).all()
        assert (raw.high>=raw[['open','close']].max(axis=1)).all() and (raw.low<=raw[['open','close']].min(axis=1)).all()
        raw.to_feather(path)
        filled=raw.set_index('date').reindex(grid); filled['synthetic']=filled.close.isna()
        prior=filled.close.ffill()
        for c in ['open','high','low','close']: filled[c]=filled[c].fillna(prior)
        filled['volume']=filled.volume.fillna(0); filled=filled.reset_index(names='date')
        filled.to_parquet(HERE/'data'/f"{pair.replace('/','_')}-audit.parquet",index=False)
        engine=HERE/'data'/path.name
        filled.drop(columns='synthetic').to_feather(engine)
        for year,g in filled[filled.date>=pd.Timestamp('2019-01-01',tz='UTC')].groupby(filled.date.dt.year):
            counts.append({'pair':pair,'year':int(year),'grid_hours':len(g),'observed':int((~g.synthetic).sum()),'synthetic':int(g.synthetic.sum())})
        audits.append({'pair':pair,'raw_sha256':sha(path),'engine_sha256':sha(engine),'start':str(raw.date.min()),'end':str(raw.date.max()),
                       'missing_count':len(missing),'missing_timestamps':list(map(str,missing)),'gap_lengths':[len(g) for g in groups],
                       'raw_zero_volume':int(raw.volume.eq(0).sum()),'duplicates':0,'post2022_candles':0,
                       'policy':'Confirmed gaps only: previous close OHLC, zero volume; synthetic flag retained in audit parquet.'})
        log('data_complete',pair=pair,observed=len(raw),synthetic=len(missing),post2022_candles=0)
    save(HERE/'audits/data.json',audits)
    pd.DataFrame(counts).to_csv(HERE/'reports/candle-counts.csv',index=False)


if __name__=='__main__': main()

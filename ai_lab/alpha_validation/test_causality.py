"""Causal and next-candle tests for the exact frozen AlphaBreakout implementation."""
import sys
import unittest
import numpy as np
import pandas as pd
from common import HERE, verify_frozen
sys.path.insert(0, str(HERE/'strategies'))
from AlphaCandidates import AlphaBreakout


def process(d):
    s=AlphaBreakout({})
    d=s.populate_indicators(d.copy(),{})
    d=s.populate_entry_trend(d,{})
    return s.populate_exit_trend(d,{})


class Tests(unittest.TestCase):
    def test_frozen_source(self):
        f=verify_frozen()
        self.assertEqual(f['parameters']['breakout_lookback_hours'],24)
        self.assertEqual(AlphaBreakout.breakout_window,24)
        self.assertEqual(AlphaBreakout.stoploss,-.05)
        self.assertEqual(AlphaBreakout.minimal_roi,{'0':.05})

    def test_prefix_future_and_prior_high(self):
        rng=np.random.default_rng(43); c=np.exp(np.log(100)+np.cumsum(rng.normal(0,.01,1000)))
        d=pd.DataFrame({'date':pd.date_range('2023-01-01',periods=1000,freq='h',tz='UTC'),'open':np.r_[c[0],c[:-1]],
          'high':c*1.004,'low':c*.996,'close':c,'volume':rng.uniform(5,20,len(c))})
        full=process(d)
        for cut in [240,500,800]: pd.testing.assert_frame_equal(process(d.iloc[:cut]),full.iloc[:cut])
        changed=d.copy(); changed.loc[700:,['open','high','low','close']]*=4; changed.loc[700:,'volume']*=8
        pd.testing.assert_frame_equal(process(changed).iloc[:700],full.iloc[:700])
        changed=d.copy(); changed.loc[500,'high']*=10
        self.assertEqual(process(changed).prior_high24.iloc[500],full.prior_high24.iloc[500])
        self.assertTrue(full.prior_high24.iloc[:24].isna().all())

    def test_real_data_timing(self):
        paths=list((HERE/'data').glob('*-1h.feather'))
        if not paths: self.skipTest('Download has not run.')
        self.assertEqual(len(paths),2)
        for path in paths:
            d=pd.read_feather(path); full=process(d)
            self.assertTrue(d.date.is_monotonic_increasing and d.date.is_unique)
            self.assertLess(d.date.max(),pd.Timestamp('2026-09-01',tz='UTC'))
            for cut in [240,9000,18000,27000,len(d)-1]: pd.testing.assert_series_equal(process(d.iloc[:cut]).iloc[-1],full.iloc[cut-1])
            events=full.index[full.enter_long.eq(1)]
            self.assertTrue((full.loc[events,'close'] > full.loc[events,'prior_high24']+.1*full.loc[events,'atr14']).all())
            self.assertTrue((full.loc[events,'relative_volume24']>=1.2).all())


if __name__=='__main__': unittest.main(verbosity=2)

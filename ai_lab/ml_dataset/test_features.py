"""Adversarial temporal checks; no outcome-based feature design."""
import unittest
import numpy as np
import pandas as pd
from features import build_features,NUMERIC
from build import first_passage


class Tests(unittest.TestCase):
    def setUp(self):
        rng=np.random.default_rng(19); c=100*np.exp(np.cumsum(rng.normal(0,.005,1000)))
        self.d=pd.DataFrame({'date':pd.date_range('2023-01-01',periods=1000,freq='h',tz='UTC'),'open':c,'close':c,'high':c*1.005,'low':c*.995,'volume':rng.uniform(1,100,1000),'synthetic':False})

    def test_prefix(self):
        full=build_features(self.d)
        for n in [720,744,800,900,999]: pd.testing.assert_frame_equal(build_features(self.d.iloc[:n]),full.iloc[:n])

    def test_future_price_and_volume(self):
        changed=self.d.copy(); changed.loc[800:,['open','close','high','low']]*=5; changed.loc[800:,'volume']=0
        pd.testing.assert_frame_equal(build_features(changed).iloc[:800],build_features(self.d).iloc[:800])

    def test_warmup_not_backfilled(self):
        f=build_features(self.d)
        self.assertTrue(f.volatility_percentile_720.iloc[:719].isna().all())
        self.assertTrue(f.return_std_168.iloc[:168].isna().all())

    def test_entry_timing(self):
        f=build_features(self.d)
        self.assertTrue((f.decision_time==self.d.date+pd.Timedelta(hours=1)).all())

    def test_flat_zero_volume(self):
        d=self.d.copy(); d[['open','close','high','low']]=100; d.volume=0
        f=build_features(d)
        self.assertEqual(f.rsi14.iloc[-1],50)
        self.assertEqual(f.volume_zscore_24.iloc[-1],0)
        self.assertEqual(f.body_to_range.iloc[-1],0)
        self.assertTrue(f.candles_since_prior_signal.isna().all())

    def test_same_hour_barriers_unknown(self):
        d=self.d.iloc[:2].copy(); d.high=102; d.low=98
        t={'open_date':d.date.iloc[0],'close_date':d.date.iloc[1],'open_rate':100}
        self.assertEqual(first_passage(t,d),(None,'same_hour_ambiguous'))

    def test_exit_candle_excluded(self):
        d=self.d.iloc[:2].copy(); d.high=100.5; d.low=99.5; d.loc[d.index[1],'high']=105
        t={'open_date':d.date.iloc[0],'close_date':d.date.iloc[1],'open_rate':100}
        self.assertEqual(first_passage(t,d),(None,'neither_barrier_observed'))


if __name__=='__main__': unittest.main(verbosity=2)

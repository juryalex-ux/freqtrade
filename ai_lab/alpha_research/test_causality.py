"""Independent timing tests, using synthetic and authorized pre2023 candles only."""
import sys
import unittest
import numpy as np
import pandas as pd
from common import HERE,VARIANTS,log
sys.path.insert(0,str(HERE/'strategies'))
import AlphaCandidates as alpha


def synthetic():
    rng=np.random.default_rng(1931); close=np.exp(np.log(100)+np.cumsum(rng.normal(0,.008,1500)))
    return pd.DataFrame({'date':pd.date_range('2019-01-01',periods=len(close),freq='h',tz='UTC'),
        'open':np.r_[close[0],close[:-1]],'high':np.maximum(close,np.r_[close[0],close[:-1]])*1.003,
        'low':np.minimum(close,np.r_[close[0],close[:-1]])*.997,'close':close,
        'volume':rng.uniform(10,20,len(close))})


def process(name,d):
    strategy=getattr(alpha,name)({})
    x=strategy.populate_indicators(d,{})
    x=strategy.populate_entry_trend(x,{})
    return strategy.populate_exit_trend(x,{})


class Tests(unittest.TestCase):
    def test_synthetic_prefix(self):
        d=synthetic()
        for name in VARIANTS:
            full=process(name,d)
            for cut in [250,749,1100]: pd.testing.assert_frame_equal(process(name,d.iloc[:cut]),full.iloc[:cut])

    def test_synthetic_future_mutation(self):
        d=synthetic(); changed=d.copy()
        changed.loc[800:,['open','high','low','close']]*=3; changed.loc[800:,'volume']*=7
        for name in VARIANTS: pd.testing.assert_frame_equal(process(name,d).iloc[:800],process(name,changed).iloc[:800])

    def test_prior_breakout_and_no_future_fill(self):
        d=synthetic(); base=process('AlphaBreakout',d)
        changed=d.copy(); changed.loc[500,'high']*=50
        other=process('AlphaBreakout',changed)
        self.assertEqual(base.prior_high24.iloc[500],other.prior_high24.iloc[500])
        self.assertTrue(base.prior_high24.iloc[:24].isna().all())
        self.assertTrue(base.return72.iloc[:72].isna().all())

    def test_perturbation_is_single_declared_parameter(self):
        attrs=['efficiency_min','breakout_window','stretch_atr','keltner_multiplier','persistence_min']
        for name in VARIANTS:
            if name.endswith(('Lo','Hi')):
                parent=getattr(alpha,name[:-2]); child=getattr(alpha,name)
                self.assertEqual(sum(getattr(parent,a)!=getattr(child,a) for a in attrs),1)
                self.assertEqual(child.stoploss,parent.stoploss)
                self.assertEqual(child.minimal_roi,parent.minimal_roi)

    def test_real_prefix_if_downloaded(self):
        files=list((HERE/'data').glob('*-audit.parquet'))
        if not files: self.skipTest('Run again after download')
        self.assertEqual(len(files),2)
        for path in files:
            d=pd.read_parquet(path).drop(columns='synthetic')
            self.assertLess(d.date.max(),pd.Timestamp('2023-01-01',tz='UTC'))
            for name in VARIANTS:
                full=process(name,d)
                for cut in [744,9000,18000,27000,len(d)-1]:
                    pd.testing.assert_series_equal(process(name,d.iloc[:cut]).iloc[-1],full.iloc[cut-1])


if __name__=='__main__': unittest.main(verbosity=2)

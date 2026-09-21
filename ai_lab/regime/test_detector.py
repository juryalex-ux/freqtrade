"""Causal invariants with synthetic data, independent of trade outcomes."""
import unittest
import numpy as np
import pandas as pd
from detector import detect,Incremental


class Tests(unittest.TestCase):
    def setUp(self):
        rng=np.random.default_rng(7)
        c=100*np.exp(np.cumsum(rng.normal(0,0.004,800)))
        self.frame=pd.DataFrame({"date":pd.date_range("2023-01-01",periods=800,freq="h",tz="UTC"),"open":c,"high":c*1.004,"low":c*.996,"close":c,"volume":1})

    def test_every_prefix(self):
        full=detect(self.frame)
        for n in range(200,801,13):
            pd.testing.assert_frame_equal(detect(self.frame.iloc[:n]),full.iloc[:n])

    def test_stream_matches_batch(self):
        stream=Incremental()
        values=[stream.update(r.close,r.high,r.low) for r in self.frame.itertuples()]
        self.assertEqual(values,detect(self.frame).regime.tolist())

    def test_future_mutation(self):
        changed=self.frame.copy()
        changed.loc[400:,["open","high","low","close"]]*=10
        pd.testing.assert_frame_equal(detect(changed).iloc[:400],detect(self.frame).iloc[:400])

    def test_available_only_after_close(self):
        r=detect(self.frame)
        self.assertTrue((r.available_at==r.date+pd.Timedelta(hours=1)).all())
        self.assertTrue(r.regime.iloc[:199].isna().all())
        self.assertTrue(r.regime.iloc[199:].notna().all())

    def test_entry_hour_cannot_change_entry_regime(self):
        changed=self.frame.copy(); changed.loc[400,["high","close"]]*=10
        entry=self.frame.date.iloc[400]
        def at(d): return detect(d).set_index("available_at").loc[entry,"regime"]
        self.assertEqual(at(changed),at(self.frame))


if __name__=="__main__": unittest.main(verbosity=2)

"""Feature causality and explicit purge/embargo invariants, no model training."""
import unittest,json
from pathlib import Path
import numpy as np
import pandas as pd
from feature_builder import build_features,FEATURES,NUMERIC

HERE=Path(__file__).resolve().parent


class Tests(unittest.TestCase):
    def setUp(self):
        rng=np.random.default_rng(2718); c=100*np.exp(np.cumsum(rng.normal(0,.005,1000)))
        self.d=pd.DataFrame({'date':pd.date_range('2020-01-01',periods=1000,freq='h',tz='UTC'),'open':c,'close':c,'high':c*1.005,'low':c*.995,'volume':rng.uniform(1,100,1000),'synthetic':False})

    def test_prefix(self):
        full=build_features(self.d)
        for n in [744,800,900,999]: pd.testing.assert_frame_equal(build_features(self.d.iloc[:n]),full.iloc[:n])

    def test_future_mutation(self):
        changed=self.d.copy(); changed.loc[800:,['open','high','low','close']]*=10; changed.loc[800:,'volume']=0
        pd.testing.assert_frame_equal(build_features(changed).iloc[:800],build_features(self.d).iloc[:800])

    def test_no_future_fill(self):
        f=build_features(self.d)
        self.assertTrue(f.volatility_percentile_720.iloc[:719].isna().all())
        self.assertTrue(f.return_168h.iloc[:168].isna().all())

    def test_label_whitelist(self):
        self.assertLessEqual(len(NUMERIC),60)
        self.assertFalse(any(c.startswith('forward_') for c in FEATURES))
        self.assertNotIn('net_profit_ratio',FEATURES)

    def test_actual_folds(self):
        datasets={name:pd.read_parquet(HERE/f'data/{name}.parquet').set_index('row_id') for name in ['A_portfolio','B_opportunities']}
        for fold in json.loads((HERE/'folds.json').read_text()):
            d=datasets[fold['dataset']]; a=d.loc[fold['train_ids']]; b=d.loc[fold['test_ids']]
            self.assertLess(a.label_end.max(),b.decision_time.min()-pd.Timedelta(hours=48))
            self.assertLess(b.label_end.max(),pd.Timestamp(fold['test_end_exclusive']))
            self.assertFalse(set(a.index)&set(b.index))

    def test_dataset_integrity(self):
        for name in ['A_portfolio','B_opportunities']:
            d=pd.read_parquet(HERE/f'data/{name}.parquet')
            self.assertFalse(d.row_id.duplicated().any()); self.assertTrue(d.decision_time.is_monotonic_increasing)
            self.assertTrue((d.feature_candle_open<d.decision_time).all())
            self.assertTrue((d.decision_time<pd.Timestamp('2025-01-01',tz='UTC')).all())
            self.assertFalse(d[FEATURES].isna().any().any())
            self.assertTrue(np.isfinite(d[NUMERIC].to_numpy(dtype=float)).all())


if __name__=='__main__': unittest.main(verbosity=2)

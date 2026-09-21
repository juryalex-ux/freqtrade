"""Before-unseal tests; never accesses shadow prices or outcomes."""
import unittest
import json
import pandas as pd
import numpy as np
from common import ROOT, economics, make_pipeline, build_features, NUMERIC


class Checks(unittest.TestCase):
    def test_exact_phase3c_candidate(self):
        p=json.loads((ROOT/'ai_lab/ml_models_v2/protocol.json').read_text())
        cols=p['feature_sets']['B_reduced']
        m=make_pipeline('logistic',cols)
        self.assertEqual(m.named_steps['model'].get_params(),p['model_parameters']['logistic'])
        self.assertEqual(len(cols),36)
        self.assertNotIn('net_profit_ratio',cols)
        self.assertEqual(m.named_steps['preprocess'].transformers[1][2],['pair','regime'])

    def test_close_time_drawdown_and_streak(self):
        d=pd.DataFrame({'strategy_outcome_end':pd.to_datetime(['2020-01-03','2020-01-01','2020-01-02'],utc=True),
            'pair':['BTC/USDT']*3,'net_profit_usdt':[20.,-10.,-10.],
            'net_profit_ratio':[.2,-.1,-.1],'regime':['RANGE']*3,'duration_minutes':[60]*3})
        result=economics(d)
        self.assertEqual(result['consecutive_losses'],2)
        self.assertAlmostEqual(result['closed_trade_max_drawdown_pct'],2.)
        self.assertEqual(result['net_usdt'],0.)
        self.assertEqual(economics(d.iloc[:0])['trades'],0)

    def test_synthetic_prefix_and_future_mutation(self):
        count=1100; t=np.arange(count); close=100+np.sin(t/20)*3+t*.001
        d=pd.DataFrame({'date':pd.date_range('2020-01-01',periods=count,freq='h',tz='UTC'),
            'open':close,'high':close+1,'low':close-1,'close':close,'volume':10+t%7,'synthetic':False})
        full=build_features(d)
        pd.testing.assert_frame_equal(build_features(d.iloc[:900]),full.iloc[:900])
        changed=d.copy(); changed.loc[900:,'close']*=2
        pd.testing.assert_frame_equal(build_features(changed).iloc[:900],full.iloc[:900])


if __name__=='__main__': unittest.main(verbosity=2)

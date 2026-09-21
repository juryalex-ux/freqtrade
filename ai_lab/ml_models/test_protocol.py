"""Temporal boundaries, preprocessing and outcome-column isolation."""
import unittest
import numpy as np
from benchmark import load,pipeline,SETS,SCHEMA,FOLDS,utc


class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.d=load('development')

    def test_whitelist(self):
        for columns in SETS.values():
            self.assertEqual(len(columns),len(set(columns)))
            self.assertTrue(set(columns)<=set(SCHEMA['feature_columns']))
            self.assertFalse(set(columns)&set(SCHEMA['label_columns']))

    def test_purged_folds(self):
        observed=set()
        for a,b in FOLDS:
            tr=self.d[(self.d.decision_time<utc(a))&(self.d.outcome_end<utc(a))]
            te=self.d[(self.d.decision_time>=utc(a))&(self.d.decision_time<utc(b))]
            self.assertLess(tr.outcome_end.max(),te.decision_time.min())
            self.assertFalse(set(te.row_id)&observed); observed.update(te.row_id)
            self.assertTrue((te.feature_candle_open<te.decision_time).all())

    def test_training_only_scaler(self):
        columns=SETS['A_all']; a,b=FOLDS[0]
        tr=self.d[(self.d.decision_time<utc(a))&(self.d.outcome_end<utc(a))]
        te=self.d[(self.d.decision_time>=utc(a))&(self.d.decision_time<utc(b))]
        model=pipeline('logistic',columns).fit(tr[columns],tr.profitable_after_fees)
        scaler=model.named_steps['preprocess'].named_transformers_['numeric']
        numeric=[c for c in columns if c not in ('pair','regime')]
        np.testing.assert_allclose(scaler.mean_,tr[numeric].mean().to_numpy())
        before=scaler.mean_.copy(); changed=te[columns].copy(); changed[numeric]*=1000
        changed['regime']='UNSEEN_CATEGORY'; model.predict_proba(changed)
        np.testing.assert_array_equal(before,scaler.mean_)


if __name__=='__main__': unittest.main(verbosity=2)

"""Structural leakage and reproducibility checks for Phase 3C."""
import json
import unittest
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SOURCE = ROOT / "ai_lab/ml_dataset_v2"


class ProtocolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = pd.read_parquet(SOURCE / "data/A_portfolio.parquet")
        cls.schema = json.loads((SOURCE / "schema.json").read_text())
        cls.folds = [x for x in json.loads((SOURCE / "folds.json").read_text())
                     if x["dataset"] == "A_portfolio"]

    def test_one_dataset_copy(self):
        self.assertEqual(len(self.data), 1271)
        self.assertTrue(self.data.row_id.is_unique)
        self.assertEqual(set(self.data.year), set(range(2019, 2025)))

    def test_predictor_whitelist(self):
        forbidden = {"net_profit_ratio", "net_profit_usdt", "strategy_outcome_end", "label_end",
                     "forward_6h_return", "forward_12h_return", "forward_24h_return",
                     "forward_48h_return", "mfe_ratio", "mae_ratio", "duration_minutes",
                     "profitable_after_fees", "return_above_0_5_percent", "return_above_1_percent"}
        self.assertFalse(forbidden.intersection(self.schema["features"]))

    def test_feature_availability(self):
        self.assertTrue((self.data.feature_candle_open + pd.Timedelta(hours=1)
                         <= self.data.decision_time).all())
        self.assertFalse(self.data[self.schema["features"]].isna().any().any())

    def test_exact_chronological_folds(self):
        prior_train = set()
        for fold in self.folds:
            train, test = set(fold["train_ids"]), set(fold["test_ids"])
            self.assertFalse(train & test)
            self.assertTrue(prior_train.issubset(train))
            prior_train = train
            train_rows = self.data[self.data.row_id.isin(train)]
            test_rows = self.data[self.data.row_id.isin(test)]
            boundary = pd.Timestamp(fold["boundary"])
            self.assertTrue((train_rows.label_end < boundary - pd.Timedelta(hours=48)).all())
            self.assertTrue((test_rows.decision_time >= boundary).all())
            self.assertTrue((test_rows.label_end < pd.Timestamp(fold["test_end_exclusive"])).all())

    def test_no_2025_or_2026(self):
        self.assertLess(self.data.decision_time.max(), pd.Timestamp("2025-01-01", tz="UTC"))
        self.assertLess(self.data.feature_candle_open.max(), pd.Timestamp("2025-01-01", tz="UTC"))

    def test_outputs_when_present(self):
        path = HERE / "results/predictions.parquet"
        if not path.exists():
            self.skipTest("benchmark has not run")
        predictions = pd.read_parquet(path)
        self.assertEqual(len(predictions), 360 * 0 + sum(x["test_rows"] for x in self.folds) * 72)
        self.assertTrue(predictions.probability.between(0, 1).all())
        self.assertEqual(predictions.groupby(["target", "feature_set", "model", "row_id"]).size().max(), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)

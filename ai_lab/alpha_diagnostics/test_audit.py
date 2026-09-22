"""Integrity tests for the frozen diagnostic evidence and causal entry context."""
from __future__ import annotations

import importlib.util
import json
import unittest
import pandas as pd
from common import HERE, ROOT, SOURCE, STRATEGIES, protocol, sha


class AuditTests(unittest.TestCase):
    def test_source_hashes_and_branch(self):
        manifest = protocol()
        for relative, digest in manifest["source_evidence_sha256"].items():
            self.assertEqual(sha(ROOT / relative), digest)
        for relative, digest in manifest["reference_source_sha256"].items():
            self.assertEqual(sha(ROOT / relative), digest)

    def test_trade_counts_and_no_later_data(self):
        trades = pd.read_parquet(HERE / "tables/trade-diagnostics.parquet")
        self.assertEqual(set(trades.strategy), set(STRATEGIES))
        self.assertEqual(len(trades), 1723)
        self.assertLess(trades.open_date.max(), pd.Timestamp("2023-01-01", tz="UTC"))
        audit = json.loads((HERE / "audits/analysis.json").read_text())
        self.assertFalse(audit["later_period_loaded"])
        self.assertFalse(audit["entry_logic_rerun"])

    def test_candle_boundaries(self):
        for path in (SOURCE / "data").glob("*-1h.feather"):
            frame = pd.read_feather(path)
            dates = pd.to_datetime(frame.date, utc=True)
            self.assertTrue(dates.is_monotonic_increasing)
            self.assertFalse(dates.duplicated().any())
            self.assertLess(dates.max(), pd.Timestamp("2023-01-01", tz="UTC"))

    def test_outcome_columns_are_not_inputs(self):
        source = (HERE / "analyze.py").read_text(encoding="utf-8")
        self.assertNotIn("populate_entry_trend", source)
        self.assertNotIn("backtesting", source)
        self.assertNotIn("shift(-", source)


if __name__ == "__main__":
    unittest.main(verbosity=2)


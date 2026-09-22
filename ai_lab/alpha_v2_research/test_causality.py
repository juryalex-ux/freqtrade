"""Causal implementation, source-pattern, and data-boundary tests."""
from __future__ import annotations

import importlib.util
import json
import unittest
import numpy as np
import pandas as pd
from common import HERE, verify_frozen

SPEC = importlib.util.spec_from_file_location("alpha_v2", HERE / "strategies/AlphaV2.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def synthetic(rows=500):
    rng = np.random.default_rng(22)
    close = 100 * np.exp(np.cumsum(rng.normal(0.0002, 0.008, rows)))
    return pd.DataFrame({"date": pd.date_range("2019-01-01", periods=rows, freq="h", tz="UTC"),
                         "open": close * (1 + rng.normal(0, .001, rows)), "close": close,
                         "high": close * (1 + rng.uniform(.001, .012, rows)),
                         "low": close * (1 - rng.uniform(.001, .012, rows)),
                         "volume": rng.uniform(100, 500, rows)})


class CausalityTests(unittest.TestCase):
    def test_source_patterns_and_freeze(self):
        verify_frozen()
        source = (HERE / "strategies/AlphaV2.py").read_text(encoding="utf-8")
        for forbidden in ("shift(-", "center=True", "center = True", ".bfill(", "backfill", "iloc[-1]"):
            self.assertNotIn(forbidden, source)

    def test_prefix_and_future_mutation(self):
        for name in ("V2TrendPullback", "V2CompressionBreakout", "V2RegimeAdaptive"):
            strategy = getattr(MODULE, name)({})
            base = synthetic()
            full = strategy.populate_indicators(base.copy(), {})
            prefix = strategy.populate_indicators(base.iloc[:420].copy(), {})
            pd.testing.assert_frame_equal(full.iloc[:420].reset_index(drop=True), prefix.reset_index(drop=True))
            mutated = base.copy()
            mutated.loc[420:, ["open", "high", "low", "close", "volume"]] *= 7
            changed = strategy.populate_indicators(mutated, {})
            pd.testing.assert_frame_equal(full.iloc[:420].reset_index(drop=True), changed.iloc[:420].reset_index(drop=True))
            first = strategy.populate_entry_trend(full.copy(), {})
            second = strategy.populate_entry_trend(changed.copy(), {})
            pd.testing.assert_series_equal(first.enter_long.iloc[:420], second.enter_long.iloc[:420])

    def test_data_boundary_order_duplicates_missing(self):
        audits = []
        for path in sorted((HERE / "data").glob("*-1h.feather")):
            frame = pd.read_feather(path)
            dates = pd.to_datetime(frame["date"], utc=True)
            self.assertTrue(dates.is_monotonic_increasing)
            self.assertFalse(dates.duplicated().any())
            self.assertLess(dates.max(), pd.Timestamp("2023-01-01", tz="UTC"))
            expected = pd.date_range(dates.min(), dates.max(), freq="h", tz="UTC")
            audits.append({"file": path.name, "rows": len(frame), "start": dates.min(), "end": dates.max(),
                           "duplicates": int(dates.duplicated().sum()), "missing": int(len(expected.difference(dates)))})
        (HERE / "audits/data-boundary.json").write_text(json.dumps(audits, indent=2, default=str) + "\n", encoding="utf-8")

    def test_prior_extrema_and_regime_exclusivity(self):
        strategy = MODULE.V2RegimeAdaptive({})
        indicators = strategy.populate_indicators(synthetic(), {})
        expected = indicators.high.rolling(12).max().shift(1)
        pd.testing.assert_series_equal(indicators.prior_high12, expected, check_names=False)
        primary, secondary, *_ = strategy.entry_components(indicators)
        self.assertFalse((primary.fillna(False) & secondary.fillna(False)).any())


if __name__ == "__main__":
    unittest.main(verbosity=2)


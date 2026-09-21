"""Offline config, candle coverage and causal signal checks for Phase 1.5."""
import json
from pathlib import Path

import pandas as pd
from freqtrade.configuration import Configuration
from freqtrade.configuration.config_validation import validate_config_consistency
from freqtrade.enums import RunMode
from freqtrade.resolvers import StrategyResolver


def main():
    findings = {}
    for name, mode in [("backtest", RunMode.BACKTEST), ("dry-run", RunMode.DRY_RUN)]:
        config = Configuration({
            "config": [f"ai_lab/configs/{name}.json"],
            "strategy_path": "ai_lab/strategies", "datadir": "ai_lab/data",
        }, mode).get_config()
        strategy = StrategyResolver.load_strategy(config)
        validate_config_consistency(config)
        assert config["dry_run"] is True
        assert config["exchange"]["pair_whitelist"] == ["BTC/USDT", "ETH/USDT"]
        findings[name] = "Freqtrade schema and consistency PASS"

    expected = pd.date_range("2024-12-29 21:00", "2025-03-31 23:00", freq="h", tz="UTC")
    for pair in ["BTC/USDT", "ETH/USDT"]:
        path = Path("ai_lab/data") / (pair.replace("/", "_") + "-1h.feather")
        frame = pd.read_feather(path)
        assert not frame.date.duplicated().any()
        assert frame.date.is_monotonic_increasing
        assert len(expected.difference(pd.DatetimeIndex(frame.date))) == 0
        assert (frame.volume > 0).all()

        def populate(data):
            data = strategy.populate_indicators(data.copy(), {"pair": pair})
            data = strategy.populate_entry_trend(data, {"pair": pair})
            return strategy.populate_exit_trend(data, {"pair": pair})

        full = populate(frame)
        # Each sampled prefix must produce the same last indicator and signal values
        # as a full-data calculation. Includes every actual crossover candle.
        indices = set(range(51, len(frame), 37))
        indices.update(full.index[(full.enter_long == 1) | (full.exit_long == 1)])
        cols = ["sma_fast", "sma_slow", "enter_long", "exit_long"]
        for index in sorted(indices):
            prefix = populate(frame.iloc[:index + 1])
            pd.testing.assert_series_equal(full.loc[index, cols], prefix.loc[index, cols])
        findings[pair] = {
            "candles": len(frame), "first": str(frame.date.min()), "last": str(frame.date.max()),
            "required_candles": len(expected), "missing": 0, "duplicates": 0,
            "prefix_checks": len(indices), "causal_signals": "PASS",
        }
    Path("ai_lab/results/offline-validation.json").write_text(json.dumps(findings, indent=2))
    print(json.dumps(findings, indent=2))


if __name__ == "__main__":
    main()

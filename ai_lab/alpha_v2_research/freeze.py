"""Freeze Phase 5A definitions before any new backtest result exists."""
from __future__ import annotations

import json
import subprocess
from common import HERE, ROOT, BASELINE_SHA, CENTRAL, VARIANTS, REFERENCES, guard, log, now, save, sha


def main() -> None:
    guard()
    assert not (HERE / "protocol.json").exists()
    assert not list((HERE / "results").rglob("*.zip"))
    source_files = ["common.py", "freeze.py", "run.py", "report.py", "finalize.py", "test_causality.py",
                    "strategies/AlphaV2.py", "strategies/LabBaseline.py", "strategies/AlphaCandidates.py", "backtest.json"]
    protocol = {
        "freeze_utc": now(),
        "git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "branch": "ai-lab-development",
        "research_window": {"warmup": ["2018-12-01", "2019-01-01"], "scored": ["2019-01-01", "2023-01-01"]},
        "forbidden_data": "No timestamp at or after 2023-01-01 may be loaded, evaluated, or reported.",
        "execution": {"pairs": ["BTC/USDT", "ETH/USDT"], "timeframe": "1h", "spot": True,
                      "signal": "completed candle", "fill": "next candle by Freqtrade", "fee_each_side": 0.001,
                      "wallet_usdt": 1000, "stake_usdt": 100, "max_open_trades": 2},
        "architectures": {
            "V2TrendPullback": {
                "state": "EMA50>EMA200, EMA50 12h slope>=0.3%, efficiency48>=0.25, NATR<=1.5x prior72h mean",
                "setup": "Within prior 4 candles low touched EMA20 zone, stayed >=98% EMA50, and close retained >=99.5% EMA50",
                "trigger": "Bullish candle close above prior3h high, positive 3h return, close location>=60%",
                "risk": "Entry-to-prior6h-low distance 0.35-2.5 ATR; structural damage exit; emergency stop -6%",
                "exit": "Close below EMA50 or prior10h low; ROI 6%",
                "rationale": "Require established directional state, a controlled retracement, and observable resumption rather than buying the first breakout.",
                "neighborhood": {"trend_slope_min": [0.002, 0.003, 0.004]},
            },
            "V2CompressionBreakout": {
                "state": "EMA50 12h slope>=-0.3% and NATR<=1.8x prior72h mean",
                "setup": "At least 4 of previous6 candles compressed; BB20 width/(4 ATR14)<=0.80 and NATR below prior72h mean",
                "trigger": "Close above prior12h compression high+0.05ATR, true range>=1.2x prior ATR, relative volume>=1.15, close location>=75%",
                "risk": "Entry-to-prior12h-low distance 0.5-2.75 ATR; emergency stop -6%",
                "exit": "Close below EMA20 or prior12h low; ROI 6%",
                "rationale": "Demand persistent contraction before participation-backed range expansion and reject structurally wide entries.",
                "neighborhood": {"compression_ratio_max": [0.75, 0.80, 0.85]},
            },
            "V2RegimeAdaptive": {
                "state": "Exclusive trend state (EMA50>EMA200, slope>=0.25%, efficiency48>=0.25) else range state (abs slope<0.4%, efficiency24<0.30, NATR<1.2x prior72h mean)",
                "setup": "Trend: prior4h EMA20 pullback above 98% EMA50. Range: prior close below EMA20-1.35ATR with prior RSI<32",
                "trigger": "Trend: bullish prior3h-high reclaim. Range: bullish reversal above prior close. Trend owns overlaps, so one candle cannot use both setups",
                "risk": "Trend distance to prior6h low 0.35-2.5 ATR; range candle recovery <=1.5ATR; emergency stop -6%",
                "exit": "Close below prior10h low or completed mean reversion (close>=EMA20 and RSI>=50); ROI 6%",
                "rationale": "Assign exactly one setup to each of two economic states instead of applying one signal across incompatible conditions.",
                "neighborhood": {"range_stretch_atr": [1.20, 1.35, 1.50]},
            },
        },
        "central": list(CENTRAL), "variants": list(VARIANTS), "references": list(REFERENCES),
        "fee_sensitivity": [0.001, 0.0015, 0.002],
        "continuation": {"aggregate_profit_factor_min_exclusive": 1.15, "positive_expectancy": True,
                         "profitable_years": "at least 3/4, or one near-flat and three clearly positive",
                         "max_single_year_profit_share": 0.60, "both_pairs_not_materially_negative": True,
                         "nearby_values_stable": True, "drawdown_not_materially_worse_than_alpha_breakout": True,
                         "sufficient_trades": True, "not_top_trade_dominated": True,
                         "operational_definitions": {"material_pair_loss_usdt": -10.0, "minimum_total_trades": 100,
                           "variant_stability": "both nearby variants aggregate net>0, PF>1, and >=2 profitable years",
                           "drawdown_limit": "candidate max annual wallet drawdown <=1.25x AlphaBreakout",
                           "top5_gross_profit_share_max": 0.35,
                           "near_flat_year_usdt": 2.0}},
        "parameter_policy": "One predeclared three-value neighborhood per architecture; no search, ranking, or post-result change.",
        "code_hashes": {name: sha(HERE / name) for name in source_files},
        "reference_hashes": {
            "ai_lab/strategies/LabBaseline.py": BASELINE_SHA,
            "ai_lab/alpha_research/strategies/AlphaCandidates.py": sha(ROOT / "ai_lab/alpha_research/strategies/AlphaCandidates.py"),
        },
        "data_hashes": {p.name: sha(p) for p in sorted((HERE / "data").glob("*.feather"))},
    }
    save(HERE / "protocol.json", protocol)
    log("architectures_frozen", protocol_sha256=sha(HERE / "protocol.json"), results_seen=False)
    print(json.dumps(protocol["architectures"], indent=2))


if __name__ == "__main__":
    main()

"""Freeze diagnostic definitions and source evidence before analysis."""
from __future__ import annotations

import subprocess
from common import HERE, ROOT, SOURCE, STRATEGIES, YEARS, guard, now, save, sha


def main() -> None:
    guard()
    assert not (HERE / "protocol.json").exists()
    evidence = {}
    for year in YEARS:
        path = SOURCE / "results/main_fee_0.10pct" / str(year) / "metrics.json"
        evidence[path.relative_to(ROOT).as_posix()] = sha(path)
    for name in ("BTC_USDT-1h.feather", "ETH_USDT-1h.feather"):
        path = SOURCE / "data" / name
        evidence[path.relative_to(ROOT).as_posix()] = sha(path)
    references = [ROOT / "ai_lab/strategies/LabBaseline.py",
                  ROOT / "ai_lab/alpha_research/strategies/AlphaCandidates.py",
                  SOURCE / "strategies/AlphaV2.py"]
    result = {
        "freeze_utc": now(),
        "git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "branch": "ai-lab-development",
        "purpose": "Diagnosis only; no strategy, parameter, entry, exit, filter, or candidate creation.",
        "strategies": list(STRATEGIES),
        "period": ["2019-01-01", "2023-01-01"],
        "warmup": ["2018-12-01", "2019-01-01"],
        "evidence_status": "Previously used development evidence; no untouched holdout claim.",
        "entry_alignment": "Trade open_date is next-candle execution. Entry context/regime uses the completed candle ending at open_date.",
        "forward_returns": {"hours": [1, 3, 6, 12, 24, 48], "formula": "close at end of horizon / fill open_rate - 1"},
        "excursions": "MFE=max high/open_rate-1 and MAE=min low/open_rate-1 over entry candle through candle before/at exit; time is first timestamp of the extreme.",
        "first_passage": {"window_hours": 48, "barriers_pct": [0.5, 1.0, 2.0, 3.0],
                          "rule": "First candle high>=+barrier versus low<=-barrier; same-candle hits are TIE and never called favorable."},
        "exit_diagnostics": {"giveback": "MFE minus gross close/open return",
                             "profitable_intratrade_closed_negative": "MFE>0.2% round-trip fee and realized net<0",
                             "stop_recovery": "within 24h after exit, high reaches entry break-even at 0.1% fee/side",
                             "structural_continuation": "within 24h after structural exit, high exceeds exit rate by >=1%"},
        "session_utc": {"Asia": [0, 8], "Europe": [8, 16], "Americas": [16, 24]},
        "expansion_context": "Signal-candle NATR14 above its prior causal 72h median; otherwise contraction.",
        "regimes": {"base": "Exact Phase 2B detector thresholds and priority",
                    "TREND": "TREND_UP or TREND_DOWN",
                    "TRANSITIONAL": "current base label differs from base label three completed candles earlier",
                    "others": ["RANGE", "HIGH_VOLATILITY", "LOW_VOLATILITY"]},
        "volatility_percentile": "Signal-candle NATR14 empirical percentile within trailing 720 completed candles; buckets [0,20),[20,40),[40,60),[60,80),[80,100].",
        "fee_sensitivity": {"per_side": [0.001, 0.0015, 0.002, 0.0025],
                            "formula": "stake_amount * (close_rate*(1-fee)/(open_rate*(1+fee))-1); identical trades only"},
        "duration_buckets_hours": ["<6", "6-12", "12-24", "24-48", ">48"],
        "trim": "Mean after removing floor(5% of trades) from each return tail per strategy.",
        "source_evidence_sha256": evidence,
        "reference_source_sha256": {path.relative_to(ROOT).as_posix(): sha(path) for path in references},
    }
    save(HERE / "protocol.json", result)
    save(HERE / "audits/freeze.json", {"protocol_sha256": sha(HERE / "protocol.json"), "results_calculated": False})


if __name__ == "__main__":
    main()


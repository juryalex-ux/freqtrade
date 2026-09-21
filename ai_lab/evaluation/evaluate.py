"""Locked, chronological evaluation of the unchanged LabBaseline. No fitting."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone
import zipfile

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
EVAL = ROOT / "ai_lab/evaluation"
PROTOCOL = EVAL / "protocol.json"
P = json.loads(PROTOCOL.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2, default=str) + "\n")


def date(value):
    return pd.Timestamp(datetime.strptime(value, "%Y%m%d"), tz="UTC")


def guard():
    assert subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT, text=True).strip() == P["branch"]
    assert not any(k.startswith("FREQTRADE__") for k in os.environ), "Environment override rejected"
    assert sha(ROOT / "ai_lab/strategies/LabBaseline.py") == P["strategy_sha256"]
    assert sha(ROOT / "ai_lab/configs/backtest.json") == P["config_sha256"]
    c = json.loads((EVAL / "frozen/backtest.json").read_text())
    assert sha(EVAL / "frozen/backtest.json") == P["config_sha256"]
    assert c["dry_run"] is True and c["trading_mode"] == "spot"
    assert c["exchange"]["pair_whitelist"] == P["pairs"]
    assert not any(c["exchange"].get(k) for k in ["key", "secret", "password"])
    assert not c.get("add_config_files") and not c.get("freqai")


def check_ranges():
    intervals = sorted((date(a), date(b), name) for name, (a, b) in P["splits"].items())
    for a, b, _ in intervals:
        assert a < b
    for previous, following in zip(intervals, intervals[1:]):
        assert previous[1] <= following[0], "Primary splits overlap"
    for fold in P["walk_forward"]:
        a, b = map(date, fold["development"])
        c, d = map(date, fold["validation"])
        assert a < b == c < d <= date(P["splits"]["validation"][1])
    validations = [tuple(map(date, f["validation"])) for f in P["walk_forward"]]
    assert all(a[1] <= b[0] for a, b in zip(validations, validations[1:]))


def command(label, args):
    guard()
    cmd = [sys.executable, "-B", "-m", "freqtrade", *args]
    with (EVAL / "results/commands.jsonl").open("a") as audit:
        audit.write(json.dumps({"utc": datetime.now(timezone.utc).isoformat(), "label": label, "cwd": str(ROOT), "argv": cmd}) + "\n")
    print(label, flush=True)
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    with (EVAL / "results" / (label + ".log")).open("w", encoding="utf-8") as output:
        result = subprocess.run(cmd, cwd=ROOT, env=env, stdout=output, stderr=subprocess.STDOUT)
    assert result.returncode == 0, f"{label} failed; inspect log"


def common(data):
    return ["--config", str(EVAL / "frozen/backtest.json"), "--userdir", str(EVAL), "--datadir", str(data)]


def download(name, start, end):
    target = EVAL / "data" / name
    target.mkdir(parents=True, exist_ok=True)
    command("download_" + name, ["download-data", *common(target), "--pairs", *P["pairs"],
                                "--timeframes", "1h", "--timerange", start + "-" + end])
    return target


def prepare(name, bounds, source):
    start, end = map(date, bounds)
    warmup = start - pd.Timedelta(hours=P["warmup_candles"])
    expected = pd.date_range(warmup, end, freq="h", inclusive="left")
    target = EVAL / "work" / name
    target.mkdir(parents=True, exist_ok=True)
    checks = {}
    for pair in P["pairs"]:
        filename = pair.replace("/", "_") + "-1h.feather"
        source_file = source / filename
        data = pd.read_feather(source_file)
        assert not data.date.duplicated().any(), "Duplicate candles"
        assert data.date.is_monotonic_increasing, "Unsorted candles"
        subset = data.loc[(data.date >= warmup) & (data.date < end)].reset_index(drop=True)
        missing = expected.difference(pd.DatetimeIndex(subset.date))
        allowed = set(pd.to_datetime(P.get("allowed_missing_utc", []), utc=True))
        assert set(missing) <= allowed, f"Unexpected missing candles: {pair} {name}: {list(missing)}"
        assert len(subset) + len(missing) == len(expected)
        assert subset[["open", "high", "low", "close", "volume"]].notna().all().all()
        assert (subset.volume >= 0).all()
        subset.to_feather(target / filename)
        checks[pair] = {"scored_candles": int((end-start).total_seconds()/3600),
                        "warmup_candles": P["warmup_candles"], "missing": len(missing),
                        "missing_utc": list(map(str, missing)), "duplicates": 0,
                        "observed_scoring_candles": int(((subset.date >= start) & (subset.date < end)).sum()),
                        "zero_volume_candles": int((subset.volume == 0).sum()),
                        "source_sha256": sha(source_file), "slice_sha256": sha(target / filename),
                        "first": str(subset.date.min()), "last": str(subset.date.max())}
    save(EVAL / "results" / (name + "_data_checks.json"), checks)
    return target


def extract(folder):
    archive = next(folder.glob("*.zip"))
    with zipfile.ZipFile(archive) as z:
        name = next(n for n in z.namelist() if n.endswith(".json") and not n.endswith("_config.json"))
        return json.loads(z.read(name))["strategy"]["LabBaseline"]


def backtest(name, bounds, source):
    data = prepare(name, bounds, source)
    output = EVAL / "results" / name
    output.mkdir(exist_ok=True)
    assert not list(output.glob("*.zip")), "Run already exists; do not overwrite evidence"
    command(name, ["backtesting", *common(data), "--strategy", "LabBaseline", "--strategy-path",
                   str(ROOT / "ai_lab/strategies"), "--timerange", "-".join(bounds), "--fee", "0.001",
                   "--cache", "none", "--export", "trades", "--backtest-directory", str(output)])
    metrics = extract(output)
    start, end = map(date, bounds)
    assert all(start <= pd.Timestamp(t["open_date"]) <= pd.Timestamp(t["close_date"]) < end for t in metrics["trades"])
    save(output / "metrics.json", metrics)
    row = {"run": name, "start_utc": str(start), "end_exclusive_utc": str(end),
           "candles_per_pair": int((end-start).total_seconds()/3600),
           "return_pct": metrics["profit_total"]*100, "trades": metrics["total_trades"],
           "win_rate_pct": metrics["winrate"]*100, "profit_factor": metrics["profit_factor"],
           "expectancy_usdt": metrics["expectancy"], "max_wallet_drawdown_pct": metrics["wallet_stats"]["max_drawdown_account"]*100,
           "max_closed_drawdown_pct": metrics["max_drawdown_account"]*100,
           "sharpe": metrics["sharpe"], "sortino": metrics["sortino"],
           "wallet_sharpe": metrics["wallet_stats"]["sharpe"], "wallet_sortino": metrics["wallet_stats"]["sortino"],
           "average_trade_pct": metrics["profit_mean"]*100, "average_duration": metrics["holding_avg"],
           "consecutive_losses": metrics["max_consecutive_losses"],
           "market_change_pct": metrics["market_change"]*100,
           "pairs": metrics["results_per_pair"], "exits": metrics["exit_reason_summary"],
           "fees_usdt": sum(t["amount"]*(t["open_rate"]*t["fee_open"]+t["close_rate"]*t["fee_close"]) for t in metrics["trades"])}
    save(output / "summary.json", row)
    print(f"{name}: {row['return_pct']:.3f}%, {row['trades']} trades", flush=True)
    return row


def causal_checks(source):
    from freqtrade.configuration import Configuration
    from freqtrade.enums import RunMode
    from freqtrade.resolvers import StrategyResolver
    cfg = Configuration({"config": [str(EVAL / "frozen/backtest.json")],
                         "strategy_path": str(ROOT / "ai_lab/strategies"), "user_data_dir": str(EVAL)}, RunMode.BACKTEST).get_config()
    strategy = StrategyResolver.load_strategy(cfg)
    counts = {}
    for pair in P["pairs"]:
        frame = pd.read_feather(source / (pair.replace("/", "_") + "-1h.feather"))
        frame = frame.loc[frame.date < date("20250101")].reset_index(drop=True)
        def populate(df):
            df = strategy.populate_indicators(df.copy(), {"pair": pair})
            df = strategy.populate_entry_trend(df, {"pair": pair})
            return strategy.populate_exit_trend(df, {"pair": pair})
        full = populate(frame)
        indices = set(range(51, len(frame), 97)) | set(full.index[(full.enter_long == 1) | (full.exit_long == 1)])
        cols = ["sma_fast", "sma_slow", "enter_long", "exit_long"]
        for index in sorted(indices):
            prefix = populate(frame.iloc[:index+1])
            pd.testing.assert_series_equal(full.loc[index, cols], prefix.loc[index, cols])
        counts[pair] = len(indices)
    save(EVAL / "results/causal_checks.json", {"passed": True, "prefixes": counts})


def main():
    os.chdir(ROOT)
    guard()
    check_ranges()
    state = EVAL / "results/test_consumed.json"
    assert not state.exists(), "Final test already consumed. Do not rerun for selection."
    lock = {"protocol_sha256": sha(PROTOCOL), "framework_sha256": sha(Path(__file__)),
            "strategy_sha256": P["strategy_sha256"], "config_sha256": P["config_sha256"],
            "locked_utc": datetime.now(timezone.utc).isoformat()}
    save(EVAL / "frozen/lock.json", lock)
    source = download("development_validation", "20221228", "20250101")
    causal_checks(source)
    rows = []
    for name in ["development", "validation"]:
        rows.append(backtest(name, P["splits"][name], source))
    for fold in P["walk_forward"]:
        for role in ["development", "validation"]:
            rows.append(backtest(fold["id"] + "_" + role, fold[role], source))
    command("lookahead", ["lookahead-analysis", *common(EVAL / "work/validation"),
                          "--strategy", "LabBaseline", "--strategy-path", str(ROOT / "ai_lab/strategies"),
                          "--timerange", "20240101-20250101", "--fee", "0.001",
                          "--lookahead-analysis-exportfilename", str(EVAL / "results/lookahead.csv")])
    bias = pd.read_csv(EVAL / "results/lookahead.csv")
    assert len(bias) == 1 and str(bias.iloc[0]["has_bias"]).lower() in ("false", "no"), "Bias check failed"
    save(EVAL / "results/non_test_summary.json", rows)
    assert sha(PROTOCOL) == lock["protocol_sha256"] and sha(Path(__file__)) == lock["framework_sha256"]
    # Terminal evaluation only: the strategy and protocol cannot be adapted afterward.
    save(state, {**lock, "status": "started", "warning": "Test is consumed from this point; never reuse for model/parameter selection."})
    test_source = download("held_out_test", "20250328", "20260401")
    rows.append(backtest("test", P["splits"]["test"], test_source))
    save(state, {**lock, "status": "complete", "warning": "Test revealed; future development requires a fresh untouched holdout."})
    guard()
    save(EVAL / "results/summary.json", rows)
    pd.DataFrame([{k:v for k,v in row.items() if k not in ("pairs", "exits")} for row in rows]).to_csv(EVAL / "results/summary.csv", index=False)
    print("Evaluation complete; final test consumed. No fitting or optimization.", flush=True)


if __name__ == "__main__":
    main()

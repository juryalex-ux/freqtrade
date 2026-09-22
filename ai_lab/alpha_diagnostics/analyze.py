"""Compute descriptive diagnostics from frozen trades and 2018-2022 candles."""
from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path
import numpy as np
import pandas as pd
from common import HERE, ROOT, SOURCE, STRATEGIES, YEARS, protocol, save, sha

HORIZONS = (1, 3, 6, 12, 24, 48)
BARRIERS = (0.005, 0.01, 0.02, 0.03)


def load_detector():
    path = ROOT / "ai_lab/regime/detector.py"
    spec = importlib.util.spec_from_file_location("phase2b_detector", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def candle_context(frame: pd.DataFrame) -> pd.DataFrame:
    detector = load_detector()
    d = detector.detect(frame.copy())
    close = d["close"]
    tr = pd.concat([d.high - d.low, (d.high - close.shift(1)).abs(), (d.low - close.shift(1)).abs()], axis=1).max(axis=1)
    d["natr14_diag"] = tr.ewm(alpha=1 / 14, adjust=False).mean() / close
    d["natr_median72"] = d["natr14_diag"].rolling(72).median().shift(1)
    d["expansion_context"] = np.where(d["natr14_diag"] > d["natr_median72"], "EXPANSION", "CONTRACTION")
    d["vol_percentile"] = d["natr14_diag"].rolling(720, min_periods=200).apply(
        lambda values: 100 * (np.sum(values[:-1] <= values[-1]) / max(len(values) - 1, 1)), raw=True)
    base = d["regime"]
    transition = base.notna() & base.shift(3).notna() & base.ne(base.shift(3))
    d["diagnostic_regime"] = np.where(transition, "TRANSITIONAL",
        np.where(base.isin(["TREND_UP", "TREND_DOWN"]), "TREND", base))
    return d


def load_inputs():
    frames = {}
    for pair in ("BTC/USDT", "ETH/USDT"):
        path = SOURCE / "data" / f"{pair.replace('/', '_')}-1h.feather"
        frame = pd.read_feather(path)
        frame["date"] = pd.to_datetime(frame["date"], utc=True)
        assert frame.date.max() < pd.Timestamp("2023-01-01", tz="UTC")
        assert frame.date.is_monotonic_increasing and not frame.date.duplicated().any()
        frames[pair] = candle_context(frame)
    trades = []
    for year in YEARS:
        source = json.loads((SOURCE / "results/main_fee_0.10pct" / str(year) / "metrics.json").read_text())
        for strategy in STRATEGIES:
            for trade in source[strategy]["trades"]:
                trades.append({"strategy": strategy, "year": year, **trade})
    return frames, trades


def session(hour: int) -> str:
    return "Asia" if hour < 8 else "Europe" if hour < 16 else "Americas"


def duration_bucket(hours: float) -> str:
    if hours < 6: return "<6h"
    if hours < 12: return "6-12h"
    if hours < 24: return "12-24h"
    if hours <= 48: return "24-48h"
    return ">48h"


def vol_bucket(percentile: float) -> str:
    if pd.isna(percentile): return "UNAVAILABLE"
    edge = min(int(percentile // 20) * 20, 80)
    return f"{edge}-{edge + 20}"


def first_time(condition: pd.Series, dates: pd.Series):
    hit = np.flatnonzero(condition.to_numpy())
    return dates.iloc[hit[0]] if len(hit) else pd.NaT


def diagnose_trade(trade: dict, frame: pd.DataFrame) -> dict:
    open_time = pd.Timestamp(trade["open_date"])
    close_time = pd.Timestamp(trade["close_date"])
    index = frame.index[frame.date == open_time]
    assert len(index) == 1, (trade["pair"], open_time)
    i = int(index[0])
    signal_i = i - 1
    held = frame[(frame.date >= open_time) & (frame.date < close_time)]
    if held.empty:
        held = frame.iloc[i:i + 1]
    open_rate = float(trade["open_rate"])
    mfe_i = held.high.idxmax()
    mae_i = held.low.idxmin()
    mfe = float(held.loc[mfe_i, "high"] / open_rate - 1)
    mae = float(held.loc[mae_i, "low"] / open_rate - 1)
    gross_exit = float(trade["close_rate"] / open_rate - 1)
    window48 = frame.iloc[i:i + 48]
    result = {
        "strategy": trade["strategy"], "year": trade["year"], "pair": trade["pair"],
        "open_date": open_time, "close_date": close_time, "open_rate": open_rate, "close_rate": trade["close_rate"],
        "profit_ratio": trade["profit_ratio"], "profit_abs": trade["profit_abs"], "stake_amount": trade["stake_amount"],
        "exit_reason": trade["exit_reason"], "duration_hours": trade["trade_duration"] / 60,
        "mfe_ratio": mfe, "mae_ratio": mae, "time_to_mfe_hours": (held.loc[mfe_i, "date"] - open_time).total_seconds() / 3600,
        "time_to_mae_hours": (held.loc[mae_i, "date"] - open_time).total_seconds() / 3600,
        "gross_exit_ratio": gross_exit, "giveback_ratio": mfe - gross_exit,
        "profitable_intratrade_closed_negative": bool(mfe > 0.002 and trade["profit_ratio"] < 0),
        "hour_utc": open_time.hour, "day_of_week": open_time.day_name(), "session_utc": session(open_time.hour),
        "duration_bucket": duration_bucket(trade["trade_duration"] / 60),
        "entry_regime": frame.loc[signal_i, "diagnostic_regime"],
        "base_regime": frame.loc[signal_i, "regime"],
        "natr14": frame.loc[signal_i, "natr14_diag"], "vol_percentile": frame.loc[signal_i, "vol_percentile"],
        "volatility_bucket": vol_bucket(frame.loc[signal_i, "vol_percentile"]),
        "expansion_context": frame.loc[signal_i, "expansion_context"],
    }
    for horizon in HORIZONS:
        target = i + horizon - 1
        result[f"forward_return_{horizon}h"] = float(frame.loc[target, "close"] / open_rate - 1) if target < len(frame) else np.nan
    first1 = frame.iloc[i:i + 1]
    first3 = frame.iloc[i:i + 3]
    result["first_1h_adverse"] = float(first1.low.min() / open_rate - 1)
    result["first_3h_adverse"] = float(first3.low.min() / open_rate - 1)
    result["first_1h_close_negative"] = bool(first1.close.iloc[-1] < open_rate)
    result["immediate_adverse_any"] = bool(first1.low.min() < open_rate)
    for barrier in BARRIERS:
        label = str(int(barrier * 1000) if barrier < .01 else int(barrier * 100)).replace(".", "_")
        favorable = first_time(window48.high >= open_rate * (1 + barrier), window48.date)
        adverse = first_time(window48.low <= open_rate * (1 - barrier), window48.date)
        if pd.isna(favorable) and pd.isna(adverse): status = "NEITHER"
        elif pd.isna(adverse): status = "FAVORABLE"
        elif pd.isna(favorable): status = "ADVERSE"
        elif favorable < adverse: status = "FAVORABLE"
        elif adverse < favorable: status = "ADVERSE"
        else: status = "TIE"
        result[f"passage_{barrier * 100:g}pct"] = status
    after_exit = frame[(frame.date >= close_time) & (frame.date < close_time + pd.Timedelta(hours=24))]
    break_even = open_rate * 1.001 / (1 - 0.001)
    result["stop_recovered_24h"] = bool(trade["exit_reason"] == "stop_loss" and len(after_exit) and after_exit.high.max() >= break_even)
    structural = "structural_exit" in trade["exit_reason"] or trade["exit_reason"] in ("sma_cross_down", "breakout_exit")
    result["structural_exit"] = structural
    result["structural_continuation_24h"] = bool(structural and len(after_exit) and after_exit.high.max() >= trade["close_rate"] * 1.01)
    return result


def economics(group: pd.DataFrame, profit_col="profit_abs") -> dict:
    profit = group[profit_col].astype(float)
    gains = profit[profit > 0].sum()
    losses = -profit[profit < 0].sum()
    return {"count": len(group), "net_usdt": float(profit.sum()),
            "profit_factor": float(gains / losses) if losses else None,
            "expectancy_usdt": float(profit.mean()) if len(group) else None,
            "win_rate_pct": float((profit > 0).mean() * 100) if len(group) else None,
            "mean_mfe_pct": float(group.mfe_ratio.mean() * 100) if len(group) else None,
            "mean_mae_pct": float(group.mae_ratio.mean() * 100) if len(group) else None}


def grouped(frame: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    rows = []
    for values, group in frame.groupby(keys, dropna=False):
        values = values if isinstance(values, tuple) else (values,)
        row = dict(zip(keys, values))
        row.update(economics(group))
        for horizon in HORIZONS:
            row[f"mean_forward_{horizon}h_pct"] = group[f"forward_return_{horizon}h"].mean() * 100
        rows.append(row)
    return pd.DataFrame(rows)


def main() -> None:
    manifest = protocol()
    assert manifest["period"][1] == "2023-01-01"
    for relative, digest in manifest["source_evidence_sha256"].items():
        assert sha(ROOT / relative) == digest, relative
    frames, raw_trades = load_inputs()
    rows = [diagnose_trade(trade, frames[trade["pair"]]) for trade in raw_trades]
    trades = pd.DataFrame(rows).sort_values(["strategy", "open_date", "pair"])
    trades.to_parquet(HERE / "tables/trade-diagnostics.parquet", index=False)
    grouped(trades, ["strategy"]).to_csv(HERE / "tables/strategy-summary.csv", index=False)
    grouped(trades, ["strategy", "year"]).to_csv(HERE / "tables/year-diagnostics.csv", index=False)
    grouped(trades, ["strategy", "pair"]).to_csv(HERE / "tables/asset-diagnostics.csv", index=False)
    grouped(trades, ["strategy", "entry_regime"]).to_csv(HERE / "tables/regime-diagnostics.csv", index=False)
    grouped(trades, ["strategy", "volatility_bucket"]).to_csv(HERE / "tables/volatility-diagnostics.csv", index=False)
    grouped(trades, ["strategy", "duration_bucket"]).to_csv(HERE / "tables/duration-diagnostics.csv", index=False)
    grouped(trades, ["strategy", "hour_utc"]).to_csv(HERE / "tables/hour-diagnostics.csv", index=False)
    grouped(trades, ["strategy", "day_of_week"]).to_csv(HERE / "tables/day-diagnostics.csv", index=False)
    grouped(trades, ["strategy", "session_utc"]).to_csv(HERE / "tables/session-diagnostics.csv", index=False)
    grouped(trades, ["strategy", "expansion_context"]).to_csv(HERE / "tables/expansion-diagnostics.csv", index=False)
    exit_rows = []
    passage_rows = []
    concentration_rows = []
    fee_rows = []
    for strategy, group in trades.groupby("strategy"):
        stop = group[group.exit_reason == "stop_loss"]
        structural = group[group.structural_exit]
        exit_rows.append({"strategy": strategy, "trades": len(group), "mean_realized_net_pct": group.profit_ratio.mean() * 100,
                          "mean_mfe_pct": group.mfe_ratio.mean() * 100, "mean_mae_pct": group.mae_ratio.mean() * 100,
                          "mean_giveback_pct": group.giveback_ratio.mean() * 100,
                          "profitable_intratrade_closed_negative_count": int(group.profitable_intratrade_closed_negative.sum()),
                          "profitable_intratrade_closed_negative_pct": group.profitable_intratrade_closed_negative.mean() * 100,
                          "stoploss_count": len(stop), "stoploss_recovered_24h_count": int(stop.stop_recovered_24h.sum()),
                          "stoploss_recovered_24h_pct": stop.stop_recovered_24h.mean() * 100 if len(stop) else None,
                          "structural_exit_count": len(structural),
                          "structural_continuation_24h_count": int(structural.structural_continuation_24h.sum()),
                          "structural_continuation_24h_pct": structural.structural_continuation_24h.mean() * 100 if len(structural) else None,
                          "mean_time_to_mfe_hours": group.time_to_mfe_hours.mean(), "mean_time_to_mae_hours": group.time_to_mae_hours.mean()})
        for barrier in BARRIERS:
            column = f"passage_{barrier * 100:g}pct"
            counts = group[column].value_counts()
            resolved = counts.get("FAVORABLE", 0) + counts.get("ADVERSE", 0)
            passage_rows.append({"strategy": strategy, "barrier_pct": barrier * 100, "trades": len(group),
                                 "favorable": int(counts.get("FAVORABLE", 0)), "adverse": int(counts.get("ADVERSE", 0)),
                                 "tie": int(counts.get("TIE", 0)), "neither": int(counts.get("NEITHER", 0)),
                                 "favorable_pct_all": counts.get("FAVORABLE", 0) / len(group) * 100,
                                 "favorable_pct_resolved": counts.get("FAVORABLE", 0) / resolved * 100 if resolved else None})
        ordered = group.profit_abs.sort_values()
        trim_n = math.floor(len(ordered) * .05)
        trimmed = ordered.iloc[trim_n:len(ordered) - trim_n] if trim_n else ordered
        net = ordered.sum()
        concentration_rows.append({"strategy": strategy, "trades": len(group), "net_usdt": net,
                                   "top5_usdt": ordered.tail(5).sum(), "top10_usdt": ordered.tail(10).sum(),
                                   "worst5_usdt": ordered.head(5).sum(), "worst10_usdt": ordered.head(10).sum(),
                                   "top5_pct_of_net": ordered.tail(5).sum() / net * 100 if net > 0 else None,
                                   "top10_pct_of_net": ordered.tail(10).sum() / net * 100 if net > 0 else None,
                                   "median_trade_usdt": ordered.median(), "trimmed_mean_usdt": trimmed.mean(), "trim_each_tail": trim_n})
        for fee in (.001, .0015, .002, .0025):
            ratio = group.close_rate * (1 - fee) / (group.open_rate * (1 + fee)) - 1
            same_trade_profit = group.stake_amount * ratio
            temp = group.copy(); temp["fee_profit"] = same_trade_profit
            values = economics(temp, "fee_profit")
            fee_rows.append({"strategy": strategy, "fee_each_side_pct": fee * 100, **values})
    pd.DataFrame(exit_rows).to_csv(HERE / "tables/exit-quality.csv", index=False)
    pd.DataFrame(passage_rows).to_csv(HERE / "tables/first-passage.csv", index=False)
    pd.DataFrame(concentration_rows).to_csv(HERE / "tables/top-trade-dependence.csv", index=False)
    pd.DataFrame(fee_rows).to_csv(HERE / "tables/fee-sensitivity-same-trades.csv", index=False)
    adverse = trades.groupby("strategy").agg(trades=("strategy", "size"), mean_first_1h_adverse_pct=("first_1h_adverse", lambda x: x.mean() * 100),
        mean_first_3h_adverse_pct=("first_3h_adverse", lambda x: x.mean() * 100), immediate_adverse_any_pct=("immediate_adverse_any", lambda x: x.mean() * 100),
        first_1h_close_negative_pct=("first_1h_close_negative", lambda x: x.mean() * 100)).reset_index()
    adverse.to_csv(HERE / "tables/adverse-selection.csv", index=False)
    save(HERE / "audits/analysis.json", {"trades": len(trades), "strategies": list(STRATEGIES),
         "minimum_timestamp": min(frame.date.min() for frame in frames.values()),
         "maximum_timestamp": max(frame.date.max() for frame in frames.values()),
         "duplicates": {pair: int(frame.date.duplicated().sum()) for pair, frame in frames.items()},
         "source_hashes_verified": True, "parameters_changed": False, "strategy_code_executed": False,
         "entry_logic_rerun": False, "later_period_loaded": False})


if __name__ == "__main__":
    main()

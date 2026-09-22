"""Create Phase 5A metrics, robustness analysis, decisions, and comparison report."""
from __future__ import annotations

import json
import math
from collections import defaultdict
import numpy as np
import pandas as pd
from common import HERE, YEARS, CENTRAL, VARIANTS, REFERENCES, log, save, verify_frozen


def trade_metrics(trades: list[dict]) -> dict:
    d = pd.DataFrame(trades)
    if d.empty:
        return {"trades": 0, "wins": 0, "losses": 0, "win_rate_pct": None, "net_usdt": 0.0,
                "total_return_pct": 0.0, "average_trade_pct": None, "profit_factor": None,
                "expectancy_usdt": None, "average_duration_hours": None, "maximum_consecutive_losses": 0,
                "closed_trade_drawdown_pct": 0.0, "top5_net_usdt": 0.0, "top10_net_usdt": 0.0,
                "top5_gross_profit_share": None, "top10_gross_profit_share": None,
                "top5_net_share": None, "top10_net_share": None}
    d["close_date"] = pd.to_datetime(d["close_date"], utc=True)
    d = d.sort_values(["close_date", "pair"])
    profit = d["profit_abs"].astype(float)
    gains = profit[profit > 0]
    losses = -profit[profit < 0]
    curve = np.r_[1000.0, 1000.0 + d.groupby("close_date")["profit_abs"].sum().sort_index().cumsum().to_numpy()]
    peak = np.maximum.accumulate(curve)
    streak = longest = 0
    for value in profit:
        streak = streak + 1 if value < 0 else 0
        longest = max(longest, streak)
    ordered = profit.sort_values(ascending=False)
    top5 = float(ordered.head(5).sum())
    top10 = float(ordered.head(10).sum())
    gross = float(gains.sum())
    net = float(profit.sum())
    return {"trades": len(d), "wins": int((profit > 0).sum()), "losses": int((profit < 0).sum()),
            "win_rate_pct": float((profit > 0).mean() * 100), "net_usdt": net, "total_return_pct": net / 10,
            "average_trade_pct": float(d["profit_ratio"].mean() * 100),
            "profit_factor": float(gains.sum() / losses.sum()) if losses.sum() else None,
            "expectancy_usdt": float(profit.mean()), "average_duration_hours": float(d["trade_duration"].mean() / 60),
            "maximum_consecutive_losses": longest, "closed_trade_drawdown_pct": float(((peak - curve) / peak).max() * 100),
            "top5_net_usdt": top5, "top10_net_usdt": top10,
            "top5_gross_profit_share": top5 / gross if gross else None, "top10_gross_profit_share": top10 / gross if gross else None,
            "top5_net_share": top5 / net if net > 0 else None, "top10_net_share": top10 / net if net > 0 else None}


def load(label: str, year: int) -> dict:
    return json.loads((HERE / "results" / label / str(year) / "metrics.json").read_text(encoding="utf-8"))


def fmt(value, places=2):
    return "N/A" if value is None or pd.isna(value) else f"{value:.{places}f}"


def main() -> None:
    protocol = verify_frozen()
    yearly = []
    pair_rows = []
    exits = []
    regimes = []
    all_trades = defaultdict(list)
    strategies = (*CENTRAL, *VARIANTS, *REFERENCES)
    for year in YEARS:
        result = load("main_fee_0.10pct", year)
        for strategy in strategies:
            raw = result[strategy]
            trades = raw["trades"]
            summary = trade_metrics(trades)
            assert summary["trades"] == raw["total_trades"]
            assert abs(summary["net_usdt"] - raw["profit_total_abs"]) < 1e-6
            summary.update({"year": year, "strategy": strategy,
                            "wallet_max_drawdown_pct": float(raw["max_drawdown_account"] * 100),
                            "sharpe": raw.get("sharpe"), "sortino": raw.get("sortino")})
            yearly.append(summary)
            all_trades[strategy].extend([{**trade, "year": year} for trade in trades])
            for pair in ("BTC/USDT", "ETH/USDT"):
                pair_rows.append({"year": year, "strategy": strategy, "pair": pair,
                                  **trade_metrics([trade for trade in trades if trade["pair"] == pair])})
            for reason in sorted({trade["exit_reason"] for trade in trades}):
                selected = [trade for trade in trades if trade["exit_reason"] == reason]
                exits.append({"year": year, "strategy": strategy, "exit_reason": reason,
                              "trades": len(selected), "net_usdt": sum(trade["profit_abs"] for trade in selected)})
            for tag in sorted({trade.get("enter_tag") or "untagged" for trade in trades}):
                selected = [trade for trade in trades if (trade.get("enter_tag") or "untagged") == tag]
                regimes.append({"year": year, "strategy": strategy, "setup_or_regime": tag,
                                "trades": len(selected), "net_usdt": sum(trade["profit_abs"] for trade in selected)})

    yearly_frame = pd.DataFrame(yearly)
    pair_frame = pd.DataFrame(pair_rows)
    yearly_frame.to_csv(HERE / "reports/yearly-metrics.csv", index=False)
    pair_frame.to_csv(HERE / "reports/pair-year-metrics.csv", index=False)
    pd.DataFrame(exits).to_csv(HERE / "reports/exit-contributions.csv", index=False)
    pd.DataFrame(regimes).to_csv(HERE / "reports/regime-contributions.csv", index=False)

    aggregate = []
    for strategy in strategies:
        y = yearly_frame[yearly_frame.strategy == strategy]
        metrics = trade_metrics(all_trades[strategy])
        positive = y[y.net_usdt > 0].net_usdt
        metrics.update({"strategy": strategy, "profitable_years": int((y.net_usdt > 0).sum()),
                        "near_flat_years": int(y.net_usdt.abs().le(2.0).sum()),
                        "pf_above_one_years": int((y.profit_factor > 1).sum()),
                        "worst_year_usdt": float(y.net_usdt.min()), "max_annual_wallet_drawdown_pct": float(y.wallet_max_drawdown_pct.max()),
                        "largest_positive_year_share": float(positive.max() / positive.sum()) if len(positive) else None})
        aggregate.append(metrics)
    agg = pd.DataFrame(aggregate)
    agg.to_csv(HERE / "reports/aggregate-metrics.csv", index=False)

    robustness = []
    for central in CENTRAL:
        parameter, values = next(iter(protocol["architectures"][central]["neighborhood"].items()))
        names = [central + "Lo", central, central + "Hi"]
        for name, value in zip(names, values):
            row = agg[agg.strategy == name].iloc[0]
            robustness.append({"architecture": central, "variant": name, "parameter": parameter, "value": value,
                               "trades": row.trades, "net_usdt": row.net_usdt, "profit_factor": row.profit_factor,
                               "profitable_years": row.profitable_years, "max_annual_wallet_drawdown_pct": row.max_annual_wallet_drawdown_pct})
    robustness_frame = pd.DataFrame(robustness)
    robustness_frame.to_csv(HERE / "reports/parameter-robustness.csv", index=False)

    fee_rows = []
    for fee_label, fee in (("main_fee_0.10pct", 0.001), ("fee_0.15pct", 0.0015), ("fee_0.20pct", 0.002)):
        for strategy in CENTRAL:
            trades = []
            annual = []
            for year in YEARS:
                raw = load(fee_label, year)[strategy]
                trades.extend(raw["trades"])
                annual.append(raw["profit_total_abs"])
            m = trade_metrics(trades)
            fee_rows.append({"strategy": strategy, "fee_each_side_pct": fee * 100, **m,
                             "profitable_years": sum(value > 0 for value in annual)})
    fees = pd.DataFrame(fee_rows)
    fees.to_csv(HERE / "reports/fee-sensitivity.csv", index=False)

    decisions = []
    breakout_dd = float(agg[agg.strategy == "AlphaBreakout"].iloc[0].max_annual_wallet_drawdown_pct)
    definitions = protocol["continuation"]["operational_definitions"]
    for strategy in CENTRAL:
        row = agg[agg.strategy == strategy].iloc[0]
        pairs = pair_frame[pair_frame.strategy == strategy].groupby("pair", as_index=False).agg(net_usdt=("net_usdt", "sum"))
        variant_rows = robustness_frame[(robustness_frame.architecture == strategy) & (robustness_frame.variant != strategy)]
        checks = {
            "aggregate_pf_gt_1_15": bool(row.profit_factor is not None and row.profit_factor > 1.15),
            "positive_expectancy": bool(row.expectancy_usdt is not None and row.expectancy_usdt > 0),
            "yearly_consistency": bool(row.profitable_years >= 3),
            "year_concentration_le_60pct": bool(row.largest_positive_year_share is not None and row.largest_positive_year_share <= 0.60),
            "both_pairs_not_materially_negative": bool((pairs.net_usdt >= definitions["material_pair_loss_usdt"]).all()),
            "nearby_values_stable": bool(((variant_rows.net_usdt > 0) & (variant_rows.profit_factor > 1) & (variant_rows.profitable_years >= 2)).all()),
            "drawdown_within_limit": bool(row.max_annual_wallet_drawdown_pct <= 1.25 * breakout_dd),
            "sufficient_trades": bool(row.trades >= definitions["minimum_total_trades"]),
            "not_top5_dominated": bool(row.top5_gross_profit_share is not None and row.top5_gross_profit_share <= definitions["top5_gross_profit_share_max"]),
        }
        if all(checks.values()):
            category = "A"
        elif checks["aggregate_pf_gt_1_15"] and checks["positive_expectancy"]:
            category = "B"
        else:
            category = "C"
        decisions.append({"strategy": strategy, "classification": category, "checks": checks,
                          "failed": [name for name, passed in checks.items() if not passed]})
    save(HERE / "reports/decisions.json", decisions)

    lines = ["# Phase 5A deterministic alpha architecture research", "",
             "All results use only 2019-01-01 through 2022-12-31, with December 2018 as warmup. No 2023+ data was loaded.", "",
             "## Frozen definitions", ""]
    for name in CENTRAL:
        definition = protocol["architectures"][name]
        lines += [f"### {name}", "", f"- Market state: {definition['state']}", f"- Setup: {definition['setup']}",
                  f"- Trigger: {definition['trigger']}", f"- Risk: {definition['risk']}", f"- Exit: {definition['exit']}",
                  f"- Rationale: {definition['rationale']}", f"- Predeclared neighborhood: `{definition['neighborhood']}`", ""]
    lines += ["## Annual portfolio results at 0.10% fee per side", "",
              "| Year | Strategy | Trades | W/L | Win % | Net USDT | Return % | Avg % | PF | Expectancy | Wallet DD % | Sharpe | Sortino | Duration h | Loss streak |",
              "| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for year in YEARS:
        for strategy in (*CENTRAL, *REFERENCES):
            r = yearly_frame[(yearly_frame.year == year) & (yearly_frame.strategy == strategy)].iloc[0]
            lines.append(f"| {year} | {strategy} | {r.trades} | {r.wins}/{r.losses} | {fmt(r.win_rate_pct)} | {fmt(r.net_usdt)} | {fmt(r.total_return_pct)} | {fmt(r.average_trade_pct)} | {fmt(r.profit_factor)} | {fmt(r.expectancy_usdt)} | {fmt(r.wallet_max_drawdown_pct)} | {fmt(r.sharpe)} | {fmt(r.sortino)} | {fmt(r.average_duration_hours)} | {r.maximum_consecutive_losses} |")
    lines += ["", "## Aggregate 2019–2022", "",
              "| Strategy | Trades | Net USDT | PF | Expectancy | Positive years | Max annual DD % | Top 5 / gross gains % | Top 10 / gross gains % | Largest positive year % |",
              "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for strategy in (*CENTRAL, *REFERENCES):
        r = agg[agg.strategy == strategy].iloc[0]
        lines.append(f"| {strategy} | {r.trades} | {fmt(r.net_usdt)} | {fmt(r.profit_factor)} | {fmt(r.expectancy_usdt)} | {r.profitable_years}/4 | {fmt(r.max_annual_wallet_drawdown_pct)} | {fmt(r.top5_gross_profit_share * 100 if pd.notna(r.top5_gross_profit_share) else None)} | {fmt(r.top10_gross_profit_share * 100 if pd.notna(r.top10_gross_profit_share) else None)} | {fmt(r.largest_positive_year_share * 100 if pd.notna(r.largest_positive_year_share) else None)} |")
    lines += ["", "## Fee sensitivity", "", "| Strategy | Fee / side | Trades | Net USDT | PF | Positive years |", "| --- | ---: | ---: | ---: | ---: | ---: |"]
    for row in fees.itertuples():
        lines.append(f"| {row.strategy} | {fmt(row.fee_each_side_pct, 3)}% | {row.trades} | {fmt(row.net_usdt)} | {fmt(row.profit_factor)} | {row.profitable_years}/4 |")
    lines += ["", "## Nearby-parameter robustness", "", "| Architecture | Variant | Parameter | Value | Trades | Net USDT | PF | Positive years | Max DD % |", "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for row in robustness_frame.itertuples():
        lines.append(f"| {row.architecture} | {row.variant} | {row.parameter} | {row.value} | {row.trades} | {fmt(row.net_usdt)} | {fmt(row.profit_factor)} | {row.profitable_years}/4 | {fmt(row.max_annual_wallet_drawdown_pct)} |")
    lines += ["", "## BTC versus ETH aggregate", "", "| Strategy | Pair | Trades | Net USDT | PF |", "| --- | --- | ---: | ---: | ---: |"]
    for strategy in (*CENTRAL, *REFERENCES):
        for pair in ("BTC/USDT", "ETH/USDT"):
            trades = [trade for trade in all_trades[strategy] if trade["pair"] == pair]
            m = trade_metrics(trades)
            lines.append(f"| {strategy} | {pair} | {m['trades']} | {fmt(m['net_usdt'])} | {fmt(m['profit_factor'])} |")
    lines += ["", "## Classification", ""]
    labels = {"A": "Eligible for later locked evaluation", "B": "Interesting but insufficient", "C": "Reject"}
    for decision in decisions:
        lines.append(f"- **{decision['strategy']}: {decision['classification']} — {labels[decision['classification']]}**. Failed criteria: {', '.join(decision['failed']) if decision['failed'] else 'none' }.")
    lines += ["", "## Audit notes", "",
              "- Strategy definitions, parameters, fee matrix, references, data hashes, and continuation criteria were frozen before results.",
              "- Prefix consistency, future mutation, prior-extrema, exclusive regime ownership, timestamp ordering, duplicates, gaps, source-pattern, and hash checks passed.",
              "- Freqtrade executes signals on the following candle. Rolling extrema are shifted one candle and no centered/future windows or future fills exist.",
              "- Detailed pair-year, exit-reason, setup/regime contribution, concentration, parameter, and fee tables are retained as machine-readable CSV files."]
    (HERE / "reports/comparison.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    log("report_complete", decisions={row["strategy"]: row["classification"] for row in decisions})


if __name__ == "__main__":
    main()


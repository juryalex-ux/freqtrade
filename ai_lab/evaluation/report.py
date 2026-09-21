"""Render locked evaluation metrics without selecting or changing any strategy."""
import json
from pathlib import Path

E = Path(__file__).resolve().parent


def main():
    rows = json.loads((E / "results/summary.json").read_text())
    lines = ["# Phase 2A comparison", "", "Fixed LabBaseline; no parameter selection or model training.",
             "All periods UTC, end-exclusive. Every run resets to 1,000 USDT; fees 0.1% per side.",
             "", "## All runs", "",
             "| Run | Start | End exclusive | Candles/pair | Return % | Trades | Win % | PF | Expectancy USDT | Wallet DD % |",
             "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for r in rows:
        lines.append(f"| {r['run']} | {r['start_utc'][:10]} | {r['end_exclusive_utc'][:10]} | {r['candles_per_pair']} | {r['return_pct']:.3f} | {r['trades']} | {r['win_rate_pct']:.2f} | {r['profit_factor']:.3f} | {r['expectancy_usdt']:.4f} | {r['max_wallet_drawdown_pct']:.3f} |")
    lines += ["", "## Risk and trade detail", "",
              "| Run | Sharpe | Sortino | Wallet Sharpe | Wallet Sortino | Avg trade % | Avg duration | Consecutive losses | Fees USDT | Market change % |",
              "| --- | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: |"]
    for r in rows:
        lines.append(f"| {r['run']} | {r['sharpe']:.3f} | {r['sortino']:.3f} | {r['wallet_sharpe']:.3f} | {r['wallet_sortino']:.3f} | {r['average_trade_pct']:.3f} | {r['average_duration']} | {r['consecutive_losses']} | {r['fees_usdt']:.4f} | {r['market_change_pct']:.2f} |")
    lines += ["", "## Pair and exit contributions", "",
              "Pair contributions use the initial total wallet as denominator. Sharpe/Sortino above",
              "are Freqtrade closed-trade metrics unless labeled wallet. No annual or fold returns",
              "are averaged as if they were a continuous portfolio.", ""]
    for r in rows:
        lines += ["### " + r["run"], "", "| Pair | Trades | Return contribution % | Net USDT | Win % |", "| --- | ---: | ---: | ---: | ---: |"]
        for p in r["pairs"]:
            if p["key"] != "TOTAL":
                lines.append(f"| {p['key']} | {p['trades']} | {p['profit_total']*100:.3f} | {p['profit_total_abs']:.4f} | {p['winrate']*100:.2f} |")
        lines += ["", "| Exit reason | Trades | Net USDT | Contribution % |", "| --- | ---: | ---: | ---: |"]
        for x in r["exits"]:
            lines.append(f"| {x['key']} | {x['trades']} | {x['profit_total_abs']:.4f} | {x['profit_total']*100:.3f} |")
        lines.append("")
    primary = [r for r in rows if r["run"] in ("development", "validation", "test")]
    wf = [r for r in rows if r["run"].startswith("wf") and r["run"].endswith("validation")]
    lines += ["## Interpretation and limitations", "",
              f"Positive primary periods: {sum(r['return_pct'] > 0 for r in primary)}/{len(primary)}. "
              f"Positive walk-forward validation periods: {sum(r['return_pct'] > 0 for r in wf)}/{len(wf)}.",
              "Signs vary across periods if positive and negative windows both occur; this is descriptive",
              "regime dependence, not statistical proof of a regime model or stable future profitability.",
              "The frozen Jan–Mar 2025 reference remains -6.57%, 54 trades, 25.9% wins, PF 0.41, wallet DD 8.52%.",
              "", "One verified missing hour per pair (2023-03-24 13:00 UTC) is explicitly allowlisted.",
              "Binance's public API confirmed the gap; see gap-verification.json. Freqtrade fills it",
              "with previous-close OHLC and zero volume. Thus 2023 has 8,759 observed candles plus",
              "one synthetic hour per pair. The first walk-forward development window likewise",
              "has one missing source hour. All other windows must have complete raw coverage.",
              "The inserted hour can affect rolling indicators even though volume-gated signals",
              "cannot fire on that candle. No claim of pristine raw data is made.",
              "", "Range, branch, strategy-hash, config-hash and environment guards were checked.",
              "Causal prefix checks and Freqtrade lookahead results are in results/. These checks",
              "do not establish absence of every possible bias. No positions cross scored windows;",
              "end-of-window force exits affect comparisons. Hourly OHLCV simulation omits realistic",
              "queueing and latency and uses current market metadata. Validation windows overlap",
              "the primary validation data; these are not independent confirmations.",
              "", "The final test was downloaded/run last after protocol and strategy locking and",
              "non-test checks. It is now consumed. Do not use these test results for optimization",
              "or call them unseen again. Future AI requires a new untouched holdout."]
    (E / "reports/comparison.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines[:24]))


if __name__ == "__main__":
    main()

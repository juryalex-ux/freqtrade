"""Present only already-calculated development/validation attribution."""
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent


def num(v):
    return "N/A" if v is None else f"{v:.3f}"


def main():
    distribution=json.loads((HERE/"results/distribution.json").read_text())
    rows=json.loads((HERE/"results/performance.json").read_text())
    lines=["# Phase 2B — baseline by entry regime", "", "No strategy or parameter changes. Only 2023 Development and 2024 Validation.",
           "Return is contribution to a 1,000 USDT starting wallet; fees are included.",
           "Drawdown is closed-trade subset drawdown, not wallet or intratrade drawdown.", "",
           "## Candle-close regime distribution", "", "| Period | Pair | Regime | Candles | % |", "| --- | --- | --- | ---: | ---: |"]
    for d in distribution:
        lines.append(f"| {d['period']} | {d['pair']} | {d['regime']} | {d['candles']} | {d['percent']:.2f} |")
    for pair in ["ALL","BTC/USDT","ETH/USDT"]:
        lines += ["", "## Performance: "+pair, "", "| Period | Regime | Trades | Win % | Net USDT | Return % | Avg trade % | PF | Expectancy USDT | Subset DD % | Avg hours |",
                  "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
        for r in rows:
            if r['pair']!=pair: continue
            lines.append(f"| {r['period']} | {r['regime']} | {r['trades']} | {num(r['win_rate_pct'])} | {num(r['profit_usdt'])} | {num(r['return_pct'])} | {num(r['average_trade_pct'])} | {num(r['profit_factor'])} | {num(r['expectancy_usdt'])} | {num(r['closed_subset_drawdown_pct'])} | {num(r['average_duration_hours'])} |")
    lines += ["", "## Exit reason contributions (both pairs)", "", "| Period | Regime | Exit | Trades | Net USDT | Return contribution % |", "| --- | --- | --- | ---: | ---: | ---: |"]
    for r in rows:
        if r['pair']!='ALL': continue
        for reason,m in r['exits'].items():
            lines.append(f"| {r['period']} | {r['regime']} | {reason} | {m['trades']} | {num(m['profit_usdt'])} | {num(m['return_pct'])} |")
    lines += ["", "## Interpretation", ""]
    for label in ["TREND_UP","TREND_DOWN","RANGE","HIGH_VOLATILITY","LOW_VOLATILITY"]:
        matches=[r for r in rows if r['pair']=='ALL' and r['regime']==label]
        values='; '.join(f"{r['period']}: {r['profit_usdt']:+.3f} USDT, n={r['trades']}" for r in matches)
        lines.append(f"- {label}: {values}.")
    lines += ["", "Categories with few trades cannot establish a reliable advantage. These are descriptive",
              "entry-attribution groups, not independently backtested trading filters. A category's",
              "label can change after entry; its entire realized P&L remains assigned to its entry label.",
              "The validation report is exploratory; no threshold was selected from these outcomes.",
              "For thresholds, causality, timing, gap handling and limitations see ../README.md.",
              "", "The shadow period 2026-04-01–2026-09-01 is sealed. No labels or performance were",
              "calculated for it. The consumed Apr 2025–Mar 2026 test was not loaded."]
    (HERE/"reports/comparison.md").write_text("\n".join(lines)+"\n")
    print("\n".join(lines[:43]))


if __name__=="__main__": main()

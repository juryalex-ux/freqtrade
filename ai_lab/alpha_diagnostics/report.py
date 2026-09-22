"""Render diagnostic plots, ranked failure assessment, and human-readable report."""
from __future__ import annotations

import json
import pandas as pd
from common import HERE, STRATEGIES, protocol, save

DISPLAY = {
    "LabBaseline": "LabBaseline",
    "AlphaBreakout": "AlphaBreakout",
    "V2TrendPullback": "V2TrendPullback",
    "V2CompressionBreakout": "V2CompressionBreakout",
    "V2RegimeAdaptive": "V2RegimeAdaptive",
}
COLORS = dict(zip(STRATEGIES, ["#6b7280", "#2563eb", "#16a34a", "#d97706", "#dc2626"]))


def fmt(value, digits=2):
    return "N/A" if value is None or pd.isna(value) else f"{value:.{digits}f}"


def svg_line(path, title, x_label, y_label, series):
    width, height = 900, 520
    left, right, top, bottom = 75, 25, 55, 65
    all_x = [x for item in series for x in item[1]]
    all_y = [y for item in series for y in item[2] if pd.notna(y)]
    x_min, x_max = min(all_x), max(all_x)
    y_min, y_max = min(all_y + [0]), max(all_y + [0])
    padding = max((y_max - y_min) * .08, .05)
    y_min -= padding; y_max += padding
    sx = lambda x: left + (x - x_min) / (x_max - x_min) * (width - left - right)
    sy = lambda y: top + (y_max - y) / (y_max - y_min) * (height - top - bottom)
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
           '<rect width="100%" height="100%" fill="white"/>',
           f'<text x="{width/2}" y="28" text-anchor="middle" font-family="sans-serif" font-size="18">{title}</text>',
           f'<line x1="{left}" y1="{top}" x2="{left}" y2="{height-bottom}" stroke="#333"/>',
           f'<line x1="{left}" y1="{height-bottom}" x2="{width-right}" y2="{height-bottom}" stroke="#333"/>',
           f'<line x1="{left}" y1="{sy(0)}" x2="{width-right}" y2="{sy(0)}" stroke="#999" stroke-dasharray="4 4"/>']
    for i in range(6):
        value = y_min + i * (y_max - y_min) / 5
        y = sy(value)
        out += [f'<line x1="{left}" y1="{y}" x2="{width-right}" y2="{y}" stroke="#eee"/>',
                f'<text x="{left-8}" y="{y+4}" text-anchor="end" font-family="sans-serif" font-size="11">{value:.2f}</text>']
    for value in sorted(set(all_x)):
        x = sx(value)
        out.append(f'<text x="{x}" y="{height-bottom+22}" text-anchor="middle" font-family="sans-serif" font-size="11">{value:g}</text>')
    for index, (name, xs, ys, color) in enumerate(series):
        points = " ".join(f"{sx(x):.1f},{sy(y):.1f}" for x, y in zip(xs, ys) if pd.notna(y))
        out.append(f'<polyline fill="none" stroke="{color}" stroke-width="2" points="{points}"/>')
        for x, y in zip(xs, ys):
            if pd.notna(y): out.append(f'<circle cx="{sx(x):.1f}" cy="{sy(y):.1f}" r="3" fill="{color}"/>')
        lx, ly = left + 10 + (index % 3) * 260, height - 18 - (index // 3) * 18
        out += [f'<line x1="{lx}" y1="{ly-4}" x2="{lx+20}" y2="{ly-4}" stroke="{color}" stroke-width="3"/>',
                f'<text x="{lx+27}" y="{ly}" font-family="sans-serif" font-size="11">{name}</text>']
    out += [f'<text x="{width/2}" y="{height-38}" text-anchor="middle" font-family="sans-serif" font-size="12">{x_label}</text>',
            f'<text x="18" y="{height/2}" transform="rotate(-90 18 {height/2})" text-anchor="middle" font-family="sans-serif" font-size="12">{y_label}</text>', '</svg>']
    path.write_text("\n".join(out), encoding="utf-8")


def plots() -> None:
    years = pd.read_csv(HERE / "tables/year-diagnostics.csv")
    fees = pd.read_csv(HERE / "tables/fee-sensitivity-same-trades.csv")
    summary = pd.read_csv(HERE / "tables/strategy-summary.csv")
    exitq = pd.read_csv(HERE / "tables/exit-quality.csv")
    svg_line(HERE / "plots/yearly-expectancy.svg", "Expectancy by year", "Year", "USDT per trade",
             [(s, years[years.strategy == s].year.tolist(), years[years.strategy == s].expectancy_usdt.tolist(), COLORS[s]) for s in STRATEGIES])
    svg_line(HERE / "plots/yearly-mfe.svg", "Entry MFE by year", "Year", "Mean MFE (%)",
             [(s, years[years.strategy == s].year.tolist(), years[years.strategy == s].mean_mfe_pct.tolist(), COLORS[s]) for s in STRATEGIES])
    svg_line(HERE / "plots/fee-sensitivity.svg", "Fee sensitivity on identical trades", "Fee per side (%)", "Net USDT",
             [(s, fees[fees.strategy == s].fee_each_side_pct.tolist(), fees[fees.strategy == s].net_usdt.tolist(), COLORS[s]) for s in STRATEGIES])
    horizon_cols = [f"mean_forward_{h}h_pct" for h in (1, 3, 6, 12, 24, 48)]
    svg_line(HERE / "plots/forward-returns.svg", "Entry-aligned forward returns", "Hours after entry", "Mean gross return (%)",
             [(s, [1, 3, 6, 12, 24, 48], [summary[summary.strategy == s].iloc[0][col] for col in horizon_cols], COLORS[s]) for s in STRATEGIES])


def main() -> None:
    manifest = protocol()
    plots()
    summary = pd.read_csv(HERE / "tables/strategy-summary.csv")
    years = pd.read_csv(HERE / "tables/year-diagnostics.csv")
    assets = pd.read_csv(HERE / "tables/asset-diagnostics.csv")
    exits = pd.read_csv(HERE / "tables/exit-quality.csv")
    adverse = pd.read_csv(HERE / "tables/adverse-selection.csv")
    fees = pd.read_csv(HERE / "tables/fee-sensitivity-same-trades.csv")
    top = pd.read_csv(HERE / "tables/top-trade-dependence.csv")
    passages = pd.read_csv(HERE / "tables/first-passage.csv")
    diagnoses = [
        {"strategy": "LabBaseline", "classification": "A", "label": "Entry logic fundamentally weak",
         "primary": ["poor entry quality", "exit giveback", "high-volatility dependence", "duration dependence"],
         "evidence": "PF 0.91; symmetric first-passage is near 50/50; 57.8% of trades were profitable intratrade but closed negative; only >48h trades were strongly profitable."},
        {"strategy": "AlphaBreakout", "classification": "E", "label": "Structurally unstable / nonstationary",
         "primary": ["structural nonstationarity", "regime dependence", "volatility dependence"],
         "evidence": "2019 lost while 2020-2021 dominated development gains; high-volatility entries lost and transitional/trend entries dominated. Prior Phase 4B retrospective evidence already established later decay."},
        {"strategy": "V2TrendPullback", "classification": "B", "label": "Entry useful but exits/risk likely dominate failure",
         "primary": ["exit giveback", "regime dependence", "duration dependence", "fee fragility", "entry timing"],
         "evidence": "Mean MFE 2.60% versus 0.14% realized; 59.6% profitable intratrade closed negative; 80.5% of structural exits were followed by a +1% continuation; short-duration trades lost heavily."},
        {"strategy": "V2CompressionBreakout", "classification": "D", "label": "Too sparse to conclude",
         "primary": ["signal rarity", "duration dependence", "fee fragility", "exit giveback"],
         "evidence": "Only 77 trades; PF 1.01; 66.2% profitable intratrade closed negative; results turn negative at 0.15% fees and depend on a small set of longer trades."},
        {"strategy": "V2RegimeAdaptive", "classification": "A", "label": "Entry logic fundamentally weak",
         "primary": ["adverse selection", "asset dependence", "regime dependence", "signal rarity"],
         "evidence": "PF 0.85; 65.5% closed the first hour below entry; BTC PF 0.52 while ETH PF 1.22; transitional entries PF 0.34; only 84 trades."},
    ]
    overall = {
        "classification": "Mixed failure led by regime/nonstationarity and exit capture",
        "ranked_causes": [
            "Regime and volatility dependence: no architecture is broadly stable across contexts.",
            "Exit/holding mismatch: favorable excursions are commonly surrendered before close.",
            "Entry timing and adverse selection: newer V2 entries have weak early forward returns and frequent immediate adverse movement.",
            "Fee fragility: marginal V2 economics disappear between 0.15% and 0.20% per side.",
            "Structural nonstationarity: yearly expectancy and entry quality vary materially, especially for AlphaBreakout and V2TrendPullback.",
            "Duration dependence: profits frequently sit in longer-duration minorities while short trades lose.",
            "Asset dependence: most pronounced in V2RegimeAdaptive; weaker in Trend Pullback and AlphaBreakout.",
            "Signal rarity/top-trade dependence: decisive for Compression Breakout and limits Adaptive inference.",
        ],
    }
    save(HERE / "reports/diagnosis.json", {"overall": overall, "strategies": diagnoses})

    lines = ["# Phase 5B deterministic alpha failure diagnosis", "",
             "This is descriptive analysis of previously used 2019–2022 development evidence. It is not a new holdout, does not rerun entry logic, and does not define or recommend filters.", "",
             "## Overall diagnosis", "", f"**{overall['classification']}**", ""]
    for index, cause in enumerate(overall["ranked_causes"], 1): lines.append(f"{index}. {cause}")
    lines += ["", "## Strategy-level diagnosis", ""]
    for item in diagnoses:
        lines += [f"### {item['strategy']}: {item['classification']} — {item['label']}", "",
                  item["evidence"], "", "Ranked causes: " + ", ".join(item["primary"]) + ".", ""]
    lines += ["## Entry quality", "",
              "| Strategy | Trades | MFE % | MAE % | 1h | 3h | 6h | 12h | 24h | 48h |",
              "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for strategy in STRATEGIES:
        r = summary[summary.strategy == strategy].iloc[0]
        lines.append(f"| {strategy} | {r['count']} | {fmt(r.mean_mfe_pct)} | {fmt(r.mean_mae_pct)} | {fmt(r.mean_forward_1h_pct)} | {fmt(r.mean_forward_3h_pct)} | {fmt(r.mean_forward_6h_pct)} | {fmt(r.mean_forward_12h_pct)} | {fmt(r.mean_forward_24h_pct)} | {fmt(r.mean_forward_48h_pct)} |")
    lines += ["", "## Exit quality", "",
              "| Strategy | Realized % | MFE % | Giveback % | Profitable intratrade, closed negative | Stop recovery | Structural continuation | Time to MFE / MAE h |",
              "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for strategy in STRATEGIES:
        r = exits[exits.strategy == strategy].iloc[0]
        stop = f"{int(r.stoploss_recovered_24h_count)}/{int(r.stoploss_count)}" if r.stoploss_count else "N/A"
        lines.append(f"| {strategy} | {fmt(r.mean_realized_net_pct)} | {fmt(r.mean_mfe_pct)} | {fmt(r.mean_giveback_pct)} | {int(r.profitable_intratrade_closed_negative_count)}/{int(r.trades)} ({fmt(r.profitable_intratrade_closed_negative_pct)}%) | {stop} | {int(r.structural_continuation_24h_count)}/{int(r.structural_exit_count)} ({fmt(r.structural_continuation_24h_pct)}%) | {fmt(r.mean_time_to_mfe_hours)} / {fmt(r.mean_time_to_mae_hours)} |")
    lines += ["", "## Adverse selection", "",
              "| Strategy | First-hour adverse % | First-3h adverse % | Any first-hour adverse | First-hour close negative |",
              "| --- | ---: | ---: | ---: | ---: |"]
    for strategy in STRATEGIES:
        r = adverse[adverse.strategy == strategy].iloc[0]
        lines.append(f"| {strategy} | {fmt(r.mean_first_1h_adverse_pct)} | {fmt(r.mean_first_3h_adverse_pct)} | {fmt(r.immediate_adverse_any_pct)}% | {fmt(r.first_1h_close_negative_pct)}% |")
    lines += ["", "## Same-trade fee sensitivity", "", "| Strategy | 0.10% | 0.15% | 0.20% | 0.25% |", "| --- | ---: | ---: | ---: | ---: |"]
    for strategy in STRATEGIES:
        values = fees[fees.strategy == strategy].sort_values("fee_each_side_pct").net_usdt.tolist()
        lines.append(f"| {strategy} | " + " | ".join(fmt(value) for value in values) + " |")
    lines += ["", "## Asset dependence", "", "| Strategy | BTC net / PF | ETH net / PF |", "| --- | ---: | ---: |"]
    for strategy in STRATEGIES:
        subset = assets[assets.strategy == strategy].set_index("pair")
        lines.append(f"| {strategy} | {fmt(subset.loc['BTC/USDT','net_usdt'])} / {fmt(subset.loc['BTC/USDT','profit_factor'])} | {fmt(subset.loc['ETH/USDT','net_usdt'])} / {fmt(subset.loc['ETH/USDT','profit_factor'])} |")
    lines += ["", "## Top-trade dependence", "", "| Strategy | Net | Top 5 | Top 10 | Worst 5 | Worst 10 | Median | Trimmed mean |", "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for strategy in STRATEGIES:
        r = top[top.strategy == strategy].iloc[0]
        lines.append(f"| {strategy} | {fmt(r.net_usdt)} | {fmt(r.top5_usdt)} | {fmt(r.top10_usdt)} | {fmt(r.worst5_usdt)} | {fmt(r.worst10_usdt)} | {fmt(r.median_trade_usdt)} | {fmt(r.trimmed_mean_usdt)} |")
    lines += ["", "## Nonstationarity", "",
              "| Strategy | 2019 PF / exp | 2020 PF / exp | 2021 PF / exp | 2022 PF / exp |",
              "| --- | ---: | ---: | ---: | ---: |"]
    for strategy in STRATEGIES:
        subset = years[years.strategy == strategy].set_index("year")
        cells = [f"{fmt(subset.loc[year,'profit_factor'])} / {fmt(subset.loc[year,'expectancy_usdt'])}" for year in (2019, 2020, 2021, 2022)]
        lines.append(f"| {strategy} | " + " | ".join(cells) + " |")
    lines += ["", "## Complete diagnostic tables", "",
              "Machine-readable tables cover first-passage probabilities, regimes, volatility percentiles, duration, hour, weekday, UTC session, expansion/contraction context, assets, years, exits, fees, adverse selection, and trade concentration. The trade-level Parquet preserves every calculated field.", "",
              "## Audit conclusion", "",
              f"- Diagnostic definitions were frozen at {manifest['freeze_utc']} before outcomes were calculated.",
              "- All source result, candle, and strategy hashes matched the frozen protocol.",
              "- No strategy code was executed or changed, no entry logic was rerun, and no 2023+ candle was loaded.",
              "- All entry context uses the completed signal candle; all future fields are explicitly diagnostic outcomes only.",
              "- Same-trade fee analysis changes costs only and never changes trade selection.",
              "- No result is used to create, promote, or recommend a filter or strategy."]
    (HERE / "reports/diagnosis.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

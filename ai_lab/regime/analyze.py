"""Only development/validation attribution. Never reads test or shadow prices."""
import hashlib
import json
from pathlib import Path
import subprocess
import pandas as pd
import numpy as np
from detector import SPEC, LABELS, detect, Incremental

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def save(p, value):
    p.write_text(json.dumps(value, indent=2, default=str, allow_nan=False)+"\n")


def load_pair(pair):
    f = HERE / "data" / (pair.replace("/", "_")+"-1h.feather")
    d = pd.read_feather(f)
    d = d[(d.date >= pd.Timestamp("2022-12-01", tz="UTC")) & (d.date < pd.Timestamp("2025-01-01", tz="UTC"))]
    assert not d.date.duplicated().any() and d.date.is_monotonic_increasing
    grid = pd.date_range("2022-12-01", "2025-01-01", freq="h", inclusive="left", tz="UTC")
    missing = grid.difference(pd.DatetimeIndex(d.date))
    assert set(missing) == {pd.Timestamp("2023-03-24 13:00", tz="UTC")}
    d = d.set_index("date").reindex(grid)
    d["synthetic"] = d.close.isna()
    previous = d.close.ffill()
    for c in ["open", "high", "low", "close"]:
        d[c] = d[c].fillna(previous)
    d["volume"] = d.volume.fillna(0)
    d.index.name = "date"
    assert d[["open","high","low","close","volume"]].notna().all().all()
    return d.reset_index(), {"source_sha256": sha(f), "missing": list(map(str,missing)), "fill": "past close / zero volume"}


def metrics(trades):
    if not trades:
        return {"trades":0,"win_rate_pct":None,"return_pct":0,"profit_usdt":0,"average_trade_pct":None,
                "profit_factor":None,"expectancy_usdt":None,"closed_subset_drawdown_pct":0,"average_duration_hours":None}
    profits = np.array([t["profit_abs"] for t in trades])
    wins = float(profits[profits>0].sum()); losses = float(-profits[profits<0].sum())
    # Hypothetical closed-trade equity of this subset, on the original 1,000 USDT basis.
    closes = pd.DataFrame({"close":[t["close_date"] for t in trades],"profit":profits}).groupby("close").profit.sum().sort_index()
    equity = np.r_[1000,1000+closes.cumsum().to_numpy()]
    peaks = np.maximum.accumulate(equity)
    return {"trades":len(trades),"win_rate_pct":float((profits>0).mean()*100),"return_pct":float(profits.sum()/10),
            "profit_usdt":float(profits.sum()),"average_trade_pct":float(np.mean([t["profit_ratio"] for t in trades])*100),
            "profit_factor":wins/losses if losses else None,"profit_factor_note":"no losing trades" if not losses else "",
            "expectancy_usdt":float(profits.mean()),"closed_subset_drawdown_pct":float(((peaks-equity)/peaks).max()*100),
            "average_duration_hours":float(np.mean([t["trade_duration"] for t in trades])/60)}


def main():
    assert subprocess.check_output(["git","branch","--show-current"],cwd=ROOT,text=True).strip()=="ai-lab-development"
    baseline = ROOT/"ai_lab/strategies/LabBaseline.py"
    expected=json.loads((ROOT/"ai_lab/evaluation/protocol.json").read_text())["strategy_sha256"]
    assert sha(baseline)==expected
    lock={"specification":sha(HERE/"specification.json"),"detector":sha(HERE/"detector.py"),"baseline":expected}
    save(HERE/"results/design-lock.json",lock)
    tables={}; audits={}; distributions=[]; all_rows=[]; attributed=[]; validation={}
    for pair in ["BTC/USDT","ETH/USDT"]:
        frame,audits[pair]=load_pair(pair)
        labeled=detect(frame)
        stream=Incremental()
        incremental=[stream.update(r.close,r.high,r.low) for r in frame.itertuples()]
        assert labeled.regime.tolist()==incremental
        cols=["natr","efficiency","ema_gap","ema_slope","regime"]
        indices=set(range(199,len(frame),197))
        for i in indices:
            pd.testing.assert_series_equal(detect(frame.iloc[:i+1]).iloc[-1][cols],labeled.iloc[i][cols])
        # Adversarial future values must never change earlier classifications.
        altered=frame.copy(); cut=len(frame)//2
        altered.loc[cut:,["open","high","low","close"]]*=3
        pd.testing.assert_frame_equal(detect(altered).iloc[:cut][cols],labeled.iloc[:cut][cols])
        validation[pair]={"incremental_candles":len(frame),"prefix_checks":len(indices),"future_perturbation":"PASS"}
        tables[pair]=labeled.set_index("available_at")
        for split,(a,b) in SPEC["design_periods"].items():
            selection=labeled[(labeled.date>=pd.Timestamp(a,tz="UTC")) & (labeled.date<pd.Timestamp(b,tz="UTC"))]
            assert selection.regime.notna().all()
            for regime in LABELS:
                count=int((selection.regime==regime).sum())
                distributions.append({"period":split,"pair":pair,"regime":regime,"candles":count,"percent":count/len(selection)*100})
            selection.to_csv(HERE/"results"/f"{split}_{pair.replace('/','_')}_labels.csv",index=False)
    for split,(a,b) in SPEC["design_periods"].items():
        source=ROOT/"ai_lab/evaluation/results"/split/"metrics.json"
        original=json.loads(source.read_text()); trades=original["trades"]
        for t in trades:
            entry=pd.Timestamp(t["open_date"])
            assert pd.Timestamp(a,tz="UTC")<=entry<pd.Timestamp(b,tz="UTC")
            # Hourly open time: last fully closed candle is indexed by this entry timestamp.
            label=tables[t["pair"]].loc[entry]
            assert label.date+pd.Timedelta(hours=1)<=entry
            t["regime"]=label.regime; t["regime_candle_open"]=str(label.date); t["period"]=split
            attributed.append(t)
        assert abs(sum(t["profit_abs"] for t in trades)-original["profit_total_abs"])<1e-7
        for pair in ["ALL","BTC/USDT","ETH/USDT"]:
            for regime in LABELS:
                subset=[t for t in trades if t["regime"]==regime and (pair=="ALL" or t["pair"]==pair)]
                row={"period":split,"pair":pair,"regime":regime,**metrics(subset)}
                row["exits"]={reason:metrics([t for t in subset if t["exit_reason"]==reason]) for reason in sorted({t["exit_reason"] for t in subset})}
                all_rows.append(row)
    assert sha(HERE/"specification.json")==lock["specification"] and sha(HERE/"detector.py")==lock["detector"]
    save(HERE/"results/data-audit.json",audits); save(HERE/"results/causality-checks.json",validation)
    save(HERE/"results/distribution.json",distributions); save(HERE/"results/performance.json",all_rows)
    save(HERE/"results/attributed-trades.json",attributed)
    pd.DataFrame(distributions).to_csv(HERE/"results/distribution.csv",index=False)
    pd.DataFrame([{k:v for k,v in r.items() if k!="exits"} for r in all_rows]).to_csv(HERE/"results/performance.csv",index=False)
    print(json.dumps({"checks":validation,"distribution":distributions,"performance":[r for r in all_rows if r['pair']=='ALL']},indent=2))


if __name__=="__main__":
    main()

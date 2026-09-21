"""Causal candle-close regime labels. No trading decisions or fitting."""
import json
from pathlib import Path
import numpy as np
import pandas as pd

SPEC = json.loads(Path(__file__).with_name("specification.json").read_text())
LABELS = SPEC["priority"]


def detect(frame):
    d = frame.copy()
    c = d.close
    fast = c.ewm(span=SPEC["ema_fast"], adjust=False).mean()
    slow = c.ewm(span=SPEC["ema_slow"], adjust=False).mean()
    tr = pd.concat([d.high-d.low, (d.high-c.shift(1)).abs(), (d.low-c.shift(1)).abs()], axis=1).max(axis=1)
    d["natr"] = tr.ewm(alpha=1/SPEC["atr_period"], adjust=False).mean()/c
    k = SPEC["efficiency_hours"]
    path = c.diff().abs().rolling(k).sum()
    d["efficiency"] = ((c-c.shift(k)).abs()/path.replace(0, np.nan)).fillna(0)
    d["ema_gap"] = (fast-slow)/c
    d["ema_slope"] = slow/slow.shift(SPEC["slope_hours"])-1
    strong = d.efficiency >= SPEC["efficiency_min"]
    d["regime"] = np.select([
        d.natr >= SPEC["high_natr"], d.natr <= SPEC["low_natr"],
        strong & (d.ema_gap >= SPEC["ma_gap_min"]) & (d.ema_slope > 0),
        strong & (d.ema_gap <= -SPEC["ma_gap_min"]) & (d.ema_slope < 0),
    ], LABELS[:4], default="RANGE")
    d["regime"] = d["regime"].astype(object)
    d.loc[d.index[:SPEC["warmup"]-1], "regime"] = None
    d["available_at"] = d.date + pd.Timedelta(hours=1)
    return d


class Incremental:
    """Independent streaming implementation used to verify batch calculations."""
    def __init__(self):
        self.closes = []
        self.slows = []
        self.fast = self.slow = self.atr = None

    def update(self, close, high, low):
        previous = self.closes[-1] if self.closes else close
        tr = max(high-low, abs(high-previous), abs(low-previous))
        if self.fast is None:
            self.fast = self.slow = close
            self.atr = tr
        else:
            self.fast += 2/(SPEC["ema_fast"]+1)*(close-self.fast)
            self.slow += 2/(SPEC["ema_slow"]+1)*(close-self.slow)
            self.atr += (tr-self.atr)/SPEC["atr_period"]
        self.closes.append(close)
        self.slows.append(self.slow)
        if len(self.closes) < SPEC["warmup"]:
            return None
        k = SPEC["efficiency_hours"]
        recent = self.closes[-k-1:]
        distance = sum(abs(b-a) for a,b in zip(recent,recent[1:]))
        efficiency = abs(recent[-1]-recent[0])/distance if distance else 0
        gap = (self.fast-self.slow)/close
        slope = self.slow/self.slows[-SPEC["slope_hours"]-1]-1
        natr = self.atr/close
        if natr >= SPEC["high_natr"]:
            return "HIGH_VOLATILITY"
        if natr <= SPEC["low_natr"]:
            return "LOW_VOLATILITY"
        if efficiency >= SPEC["efficiency_min"] and gap >= SPEC["ma_gap_min"] and slope > 0:
            return "TREND_UP"
        if efficiency >= SPEC["efficiency_min"] and gap <= -SPEC["ma_gap_min"] and slope < 0:
            return "TREND_DOWN"
        return "RANGE"

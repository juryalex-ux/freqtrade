"""Past-only hourly features; no trade outcomes or holdout readers."""
from pathlib import Path
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "regime"))
from detector import detect

DEFINITIONS = {
    "ema20_distance": "close / EMA20 - 1; adjust=False",
    "ema50_distance": "close / EMA50 - 1; adjust=False",
    "ema_gap": "(EMA20 - EMA50) / close",
    "ema20_slope_6": "EMA20 / EMA20.shift(6) - 1",
    "ema50_slope_6": "EMA50 / EMA50.shift(6) - 1",
    "trend_efficiency_20": "abs(close-close.shift(20)) / rolling20 sum(abs(diff(close))); zero path -> 0",
    "body_ratio": "(close-open)/open",
    "range_ratio": "(high-low)/close",
    "body_to_range": "abs(close-open)/(high-low); zero range -> 0",
    "close_location": "(close-low)/(high-low); zero range -> 0.5",
    "atr14": "EMA(alpha=1/14, adjust=False) of max(high-low,abs(high-prev_close),abs(low-prev_close))",
    "natr14": "ATR14/close",
    "return_std_24": "rolling24 sample standard deviation of hourly simple returns, ddof=1",
    "return_std_168": "rolling168 sample standard deviation of hourly simple returns, ddof=1",
    "volatility_percentile_720": "fraction of last720 NATR14 values <= current NATR14; includes current, no global fit",
    "rsi14": "100*EMA14 gains/(EMA14 gains+EMA14 losses), alpha=1/14; flat -> 50",
    "macd_ratio": "(EMA12-EMA26)/close",
    "macd_signal_ratio": "EMA9(EMA12-EMA26)/close",
    "macd_hist_ratio": "(MACD-EMA9(MACD))/close",
    "relative_volume_24": "volume / rolling24 mean(volume); zero mean -> 0",
    "volume_zscore_24": "(volume-rolling24 mean)/rolling24 sample std; zero std -> 0",
    "volume_trend_24_168": "rolling24 mean(volume)/rolling168 mean(volume)-1; zero denominator -> 0",
    "regime_duration": "consecutive candles with current Phase2B regime, including current",
    "regime_transition": "1 if current Phase2B regime differs from previous candle, else 0",
    "hour_of_day": "UTC hour of decision time (candle open + 1h)",
    "day_of_week": "UTC weekday of decision time, Monday=0",
    "distance_high_24": "close / trailing24 max(high) - 1",
    "distance_low_24": "close / trailing24 min(low) - 1",
    "distance_high_168": "close / trailing168 max(high) - 1",
    "distance_low_168": "close / trailing168 min(low) - 1",
    "candles_since_prior_signal": "candles since last SMA20/50 upward crossover strictly before current candle; no prior -> missing",
    "source_synthetic": "1 if decision candle was known gap filled with past close / zero volume",
    "pair": "BTC/USDT or ETH/USDT categorical identifier",
    "regime": "unchanged Phase2B causal label at decision candle close",
}
for window in [1,3,6,12,24,72]:
    DEFINITIONS[f"return_{window}h"] = f"close / close.shift({window}) - 1 (also multi-window momentum)"
NUMERIC = [k for k in DEFINITIONS if k not in ("pair","regime")]
FEATURES = list(DEFINITIONS)


def build_features(d):
    c=d.close; r=c.pct_change(fill_method=None); out=pd.DataFrame(index=d.index)
    e20=c.ewm(span=20,adjust=False).mean(); e50=c.ewm(span=50,adjust=False).mean()
    regimes=detect(d)
    out['ema20_distance']=c/e20-1; out['ema50_distance']=c/e50-1
    out['ema_gap']=(e20-e50)/c
    out['ema20_slope_6']=e20/e20.shift(6)-1; out['ema50_slope_6']=e50/e50.shift(6)-1
    out['trend_efficiency_20']=regimes.efficiency
    out['body_ratio']=(c-d.open)/d.open; out['range_ratio']=(d.high-d.low)/c
    span=(d.high-d.low).replace(0,np.nan)
    out['body_to_range']=((c-d.open).abs()/span).fillna(0)
    out['close_location']=((c-d.low)/span).fillna(.5)
    out['atr14']=regimes.natr*c; out['natr14']=regimes.natr
    out['return_std_24']=r.rolling(24).std(); out['return_std_168']=r.rolling(168).std()
    out['volatility_percentile_720']=regimes.natr.rolling(720).rank(pct=True,method='max')
    delta=c.diff(); gain=delta.clip(lower=0).ewm(alpha=1/14,adjust=False).mean()
    loss=(-delta.clip(upper=0)).ewm(alpha=1/14,adjust=False).mean()
    out['rsi14']=(100*gain/(gain+loss).replace(0,np.nan)).fillna(50)
    macd=c.ewm(span=12,adjust=False).mean()-c.ewm(span=26,adjust=False).mean()
    signal=macd.ewm(span=9,adjust=False).mean()
    out['macd_ratio']=macd/c; out['macd_signal_ratio']=signal/c; out['macd_hist_ratio']=(macd-signal)/c
    vm=d.volume.rolling(24).mean(); vs=d.volume.rolling(24).std()
    out['relative_volume_24']=(d.volume/vm.replace(0,np.nan)).where(vm!=0,0)
    out['volume_zscore_24']=((d.volume-vm)/vs.replace(0,np.nan)).where(vs!=0,0)
    longvm=d.volume.rolling(168).mean()
    out['volume_trend_24_168']=(vm/longvm.replace(0,np.nan)-1).where(longvm!=0,0)
    out['regime']=regimes.regime
    transition=regimes.regime.ne(regimes.regime.shift(1))
    out['regime_transition']=transition.astype(int)
    out['regime_duration']=regimes.groupby(transition.cumsum()).cumcount()+1
    available=d.date+pd.Timedelta(hours=1)
    out['hour_of_day']=available.dt.hour; out['day_of_week']=available.dt.dayofweek
    for w in [24,168]:
        out[f'distance_high_{w}']=c/d.high.rolling(w).max()-1
        out[f'distance_low_{w}']=c/d.low.rolling(w).min()-1
    fast=c.rolling(20).mean(); slow=c.rolling(50).mean()
    cross=(fast>slow)&(fast.shift(1)<=slow.shift(1))&(d.volume>0)
    last=pd.Series(np.where(cross,np.arange(len(d)),np.nan),index=d.index).shift(1).ffill()
    out['candles_since_prior_signal']=np.arange(len(d))-last
    out['source_synthetic']=d.synthetic.astype(int)
    for w in [1,3,6,12,24,72]: out[f'return_{w}h']=c/c.shift(w)-1
    out['feature_candle_open']=d.date; out['decision_time']=available
    return out

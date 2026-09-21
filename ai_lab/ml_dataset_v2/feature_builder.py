"""Small fixed extension of Phase 2C features; no outcome-driven selection."""
from pathlib import Path
import sys
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'ml_dataset'))
from features import build_features as base_features, DEFINITIONS as ORIGINAL

REMOVED={'body_ratio':'Near duplicate of return_1h; hourly open approximately previous close.',
         'atr14':'Use normalized ATR instead of price-scale-dependent raw ATR.',
         'macd_hist_ratio':'Exact difference of macd_ratio and macd_signal_ratio.'}
ADDED={'return_168h':'close/close.shift(168)-1; one week momentum',
       'volatility_ratio_24_168':'rolling24 std(hourly returns)/rolling168 std; zero denominator ->0',
       'natr_ratio_168':'current NATR14/rolling168 mean NATR14; relative volatility level',
       'up_fraction_24':'fraction of last24 close differences strictly positive; directional persistence',
       'volume_price_interaction':'return_1h * relative_volume_24; signed volume-confirmed movement',
       'range_expansion_24':'range_ratio/rolling24 mean(range_ratio); zero denominator ->0',
       'signal_density_168':'count of baseline upward SMA crosses in last168 candles /168; includes current signal'}
DEFINITIONS={**{k:v for k,v in ORIGINAL.items() if k not in REMOVED},**ADDED}
FEATURES=list(DEFINITIONS); NUMERIC=[k for k in FEATURES if k not in ('pair','regime')]


def signal_mask(d):
    f=d.close.rolling(20).mean(); s=d.close.rolling(50).mean()
    return (f>s)&(f.shift(1)<=s.shift(1))&(d.volume>0)


def build_features(d):
    f=base_features(d).drop(columns=list(REMOVED))
    f['return_168h']=d.close/d.close.shift(168)-1
    f['volatility_ratio_24_168']=(f.return_std_24/f.return_std_168.replace(0,np.nan)).where(f.return_std_168!=0,0)
    f['natr_ratio_168']=f.natr14/f.natr14.rolling(168).mean()
    f['up_fraction_24']=(d.close.diff()>0).astype(float).rolling(24).mean()
    f['volume_price_interaction']=f.return_1h*f.relative_volume_24
    mean=f.range_ratio.rolling(24).mean()
    f['range_expansion_24']=(f.range_ratio/mean.replace(0,np.nan)).where(mean!=0,0)
    f['signal_density_168']=signal_mask(d).astype(int).rolling(168).sum()/168
    return f

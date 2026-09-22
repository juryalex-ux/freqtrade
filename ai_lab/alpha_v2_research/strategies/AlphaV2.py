"""Three frozen causal state -> setup -> trigger -> risk -> exit architectures."""
from __future__ import annotations

import numpy as np
from pandas import DataFrame
from freqtrade.strategy import IStrategy


class V2Base(IStrategy):
    INTERFACE_VERSION = 3
    timeframe = "1h"
    can_short = False
    startup_candle_count = 300
    process_only_new_candles = True
    minimal_roi = {"0": 0.06}
    stoploss = -0.06
    trailing_stop = False
    use_exit_signal = True
    exit_profit_only = False
    order_types = {"entry": "limit", "exit": "limit", "stoploss": "market", "stoploss_on_exchange": False}
    order_time_in_force = {"entry": "GTC", "exit": "GTC"}
    architecture = "base"
    trend_slope_min = 0.003
    compression_ratio_max = 0.80
    range_stretch_atr = 1.35

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        d = dataframe.copy()
        close = d["close"]
        for window in (20, 50, 200):
            d[f"ema{window}"] = close.ewm(span=window, adjust=False).mean()
        d["slope50_12"] = d["ema50"] / d["ema50"].shift(12) - 1
        path24 = close.diff().abs().rolling(24).sum()
        path48 = close.diff().abs().rolling(48).sum()
        d["efficiency24"] = (close - close.shift(24)).abs() / path24.replace(0, np.nan)
        d["efficiency48"] = (close - close.shift(48)).abs() / path48.replace(0, np.nan)
        true_range = DataFrame({
            "range": d["high"] - d["low"],
            "high_gap": (d["high"] - close.shift(1)).abs(),
            "low_gap": (d["low"] - close.shift(1)).abs(),
        }).max(axis=1)
        d["true_range"] = true_range
        d["atr14"] = true_range.ewm(alpha=1 / 14, adjust=False).mean()
        d["natr14"] = d["atr14"] / close
        d["natr_mean72"] = d["natr14"].rolling(72).mean().shift(1)
        d["rel_volume24"] = d["volume"] / d["volume"].rolling(24).mean().shift(1).replace(0, np.nan)
        delta = close.diff()
        gain = delta.clip(lower=0).ewm(alpha=1 / 14, adjust=False).mean()
        loss = (-delta.clip(upper=0)).ewm(alpha=1 / 14, adjust=False).mean()
        d["rsi14"] = 100 * gain / (gain + loss).replace(0, np.nan)
        d["close_location"] = (close - d["low"]) / (d["high"] - d["low"]).replace(0, np.nan)
        d["prior_high3"] = d["high"].rolling(3).max().shift(1)
        d["prior_high12"] = d["high"].rolling(12).max().shift(1)
        d["prior_low6"] = d["low"].rolling(6).min().shift(1)
        d["prior_low10"] = d["low"].rolling(10).min().shift(1)
        d["prior_low12"] = d["low"].rolling(12).min().shift(1)
        d["return3"] = close / close.shift(3) - 1
        d["bb_width20"] = 4 * close.rolling(20).std(ddof=0)
        d["compression_ratio"] = d["bb_width20"] / (4 * d["atr14"]).replace(0, np.nan)
        d["compressed"] = (d["compression_ratio"] <= self.compression_ratio_max) & (d["natr14"] < d["natr_mean72"])
        d["compression_persist"] = d["compressed"].shift(1).rolling(6).sum() >= 4
        d["compression_high12"] = d["high"].rolling(12).max().shift(1)
        d["compression_low12"] = d["low"].rolling(12).min().shift(1)
        d["risk_atr6"] = (close - d["prior_low6"]) / d["atr14"].replace(0, np.nan)
        d["risk_atr12"] = (close - d["compression_low12"]) / d["atr14"].replace(0, np.nan)
        return d

    def entry_components(self, d: DataFrame) -> tuple:
        bullish_candle = (d["close"] > d["open"]) & (d["close_location"] >= 0.60)
        if self.architecture == "trend_pullback":
            state = ((d["ema50"] > d["ema200"]) & (d["slope50_12"] >= self.trend_slope_min)
                     & (d["efficiency48"] >= 0.25) & (d["natr14"] <= 1.5 * d["natr_mean72"]))
            setup_now = ((d["low"] <= 1.005 * d["ema20"]) & (d["low"] >= 0.98 * d["ema50"])
                         & (d["close"] >= 0.995 * d["ema50"]))
            setup = setup_now.shift(1).rolling(4).max().eq(1)
            trigger = bullish_candle & (d["close"] > d["prior_high3"]) & (d["return3"] > 0)
            risk = d["risk_atr6"].between(0.35, 2.5)
            tag = "trend_pullback"
        elif self.architecture == "compression_breakout":
            state = (d["slope50_12"] >= -0.003) & (d["natr14"] <= 1.8 * d["natr_mean72"])
            setup = d["compression_persist"]
            trigger = ((d["close"] > d["compression_high12"] + 0.05 * d["atr14"])
                       & (d["true_range"] >= 1.20 * d["atr14"].shift(1))
                       & (d["rel_volume24"] >= 1.15) & (d["close_location"] >= 0.75))
            risk = d["risk_atr12"].between(0.5, 2.75)
            tag = "compression_breakout"
        elif self.architecture == "regime_adaptive":
            trend_state = ((d["ema50"] > d["ema200"]) & (d["slope50_12"] >= 0.0025)
                           & (d["efficiency48"] >= 0.25))
            range_state = (~trend_state) & (d["slope50_12"].abs() < 0.004) & (d["efficiency24"] < 0.30) & (d["natr14"] < 1.2 * d["natr_mean72"])
            trend_setup_now = (d["low"] <= 1.005 * d["ema20"]) & (d["low"] >= 0.98 * d["ema50"])
            trend_setup = trend_setup_now.shift(1).rolling(4).max().eq(1)
            trend_trigger = bullish_candle & (d["close"] > d["prior_high3"]) & (d["return3"] > 0)
            range_setup = (d["close"].shift(1) < d["ema20"].shift(1) - self.range_stretch_atr * d["atr14"].shift(1)) & (d["rsi14"].shift(1) < 32)
            range_trigger = bullish_candle & (d["close"] > d["close"].shift(1))
            trend_signal = trend_state & trend_setup & trend_trigger & d["risk_atr6"].between(0.35, 2.5)
            range_signal = range_state & range_setup & range_trigger & ((d["close"] - d["low"]) <= 1.5 * d["atr14"])
            return trend_signal, range_signal, "adaptive_trend", "adaptive_range"
        else:
            raise ValueError(self.architecture)
        return state & setup & trigger & risk, None, tag, None

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        d = dataframe.copy()
        primary, secondary, primary_tag, secondary_tag = self.entry_components(d)
        primary = primary.fillna(False) & (d["volume"] > 0)
        primary = primary & ~primary.shift(1, fill_value=False)
        d["enter_long"] = primary.astype(int)
        d.loc[primary, "enter_tag"] = primary_tag
        if secondary is not None:
            secondary = secondary.fillna(False) & (d["volume"] > 0)
            secondary = secondary & ~secondary.shift(1, fill_value=False)
            if (primary & secondary).any():
                raise AssertionError("Regime ownership overlap")
            d.loc[secondary, "enter_long"] = 1
            d.loc[secondary, "enter_tag"] = secondary_tag
        return d

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        d = dataframe.copy()
        if self.architecture == "trend_pullback":
            condition = (d["close"] < d["ema50"]) | (d["close"] < d["prior_low10"])
        elif self.architecture == "compression_breakout":
            condition = (d["close"] < d["ema20"]) | (d["close"] < d["prior_low12"])
        elif self.architecture == "regime_adaptive":
            condition = (d["close"] < d["prior_low10"]) | ((d["close"] >= d["ema20"]) & (d["rsi14"] >= 50))
        else:
            raise ValueError(self.architecture)
        d["exit_long"] = (condition.fillna(False) & (d["volume"] > 0)).astype(int)
        d.loc[d["exit_long"].eq(1), "exit_tag"] = self.architecture + "_structural_exit"
        return d


class V2TrendPullback(V2Base): architecture = "trend_pullback"
class V2TrendPullbackLo(V2TrendPullback): trend_slope_min = 0.002
class V2TrendPullbackHi(V2TrendPullback): trend_slope_min = 0.004
class V2CompressionBreakout(V2Base): architecture = "compression_breakout"
class V2CompressionBreakoutLo(V2CompressionBreakout): compression_ratio_max = 0.75
class V2CompressionBreakoutHi(V2CompressionBreakout): compression_ratio_max = 0.85
class V2RegimeAdaptive(V2Base): architecture = "regime_adaptive"
class V2RegimeAdaptiveLo(V2RegimeAdaptive): range_stretch_atr = 1.20
class V2RegimeAdaptiveHi(V2RegimeAdaptive): range_stretch_atr = 1.50


"""Five causal long-only hypotheses; fixed definitions, no search or fitting."""
import numpy as np
from pandas import DataFrame
from freqtrade.strategy import IStrategy


class AlphaBase(IStrategy):
    INTERFACE_VERSION=3
    timeframe='1h'
    can_short=False
    startup_candle_count=240
    process_only_new_candles=True
    minimal_roi={'0':0.05}
    stoploss=-0.05
    trailing_stop=False
    use_exit_signal=True
    exit_profit_only=False
    order_types={'entry':'limit','exit':'limit','stoploss':'market','stoploss_on_exchange':False}
    order_time_in_force={'entry':'GTC','exit':'GTC'}
    family='base'
    efficiency_min=.30
    breakout_window=24
    stretch_atr=1.5
    keltner_multiplier=1.5
    persistence_min=.60

    def populate_indicators(self, dataframe:DataFrame, metadata:dict)->DataFrame:
        d=dataframe.copy(); c=d.close
        for n in [20,50]: d[f'ema{n}']=c.ewm(span=n,adjust=False).mean()
        d['slope50_6']=d.ema50/d.ema50.shift(6)-1
        path=c.diff().abs().rolling(20).sum()
        d['efficiency20']=(c-c.shift(20)).abs()/path.replace(0,np.nan)
        tr=DataFrame({'range':d.high-d.low,'high_gap':(d.high-c.shift(1)).abs(),'low_gap':(d.low-c.shift(1)).abs()}).max(axis=1)
        d['atr14']=tr.ewm(alpha=1/14,adjust=False).mean()
        d['natr14']=d.atr14/c
        d['natr_reference24']=d.natr14.rolling(24).mean().shift(1)
        d['relative_volume24']=d.volume/d.volume.rolling(24).mean().shift(1).replace(0,np.nan)
        delta=c.diff()
        gains=delta.clip(lower=0).ewm(alpha=1/14,adjust=False).mean()
        losses=(-delta.clip(upper=0)).ewm(alpha=1/14,adjust=False).mean()
        d['rsi14']=100*gains/(gains+losses).replace(0,np.nan)
        for n in [6,20,24,28]: d[f'prior_high{n}']=d.high.rolling(n).max().shift(1)
        d['prior_low12']=d.low.rolling(12).min().shift(1)
        d['close_location']=(c-d.low)/(d.high-d.low).replace(0,np.nan)
        for n in [3,24,72]: d[f'return{n}']=c/c.shift(n)-1
        d['up_fraction24']=(c.diff()>0).astype(float).rolling(24).mean()
        d['bb_width20']=4*c.rolling(20).std(ddof=0)
        d['squeeze']=d.bb_width20 < 2*self.keltner_multiplier*d.atr14
        d['recent_squeeze']=d['squeeze'].astype(int).shift(1).rolling(6).max().eq(1)
        return d

    def raw_entry(self,d):
        if self.family=='trend':
            return ((d.ema20>d.ema50)&(d.slope50_6>0)&(d.efficiency20>=self.efficiency_min)
                &(d.low.shift(1)<=d.ema20.shift(1))&(d.close>d.ema20)&(d.return3>0))
        if self.family=='breakout':
            return ((d.close>d[f'prior_high{self.breakout_window}']+.1*d.atr14)
                &(d.natr14>d.natr_reference24)&(d.relative_volume24>=1.2)&(d.close_location>=.75))
        if self.family=='reversion':
            return ((d.close<d.ema20-self.stretch_atr*d.atr14)&(d.rsi14<30)
                &(d.close>d.close.shift(1))&(d.efficiency20<.25)&(d.slope50_6.abs()<.005)&(d.natr14<.015))
        if self.family=='squeeze':
            return (d.recent_squeeze&(d.close>d.prior_high20)&(d.natr14>d.natr14.shift(1))&(d.relative_volume24>=1.2))
        if self.family=='momentum':
            return ((d.return24>0)&(d.return72>0)&(d.up_fraction24>=self.persistence_min)
                &(d.relative_volume24>=1.2)&(d.close>d.open)&(d.close_location>=.70)&(d.close>d.prior_high6))
        raise ValueError(self.family)

    def populate_entry_trend(self,dataframe:DataFrame,metadata:dict)->DataFrame:
        d=dataframe.copy()
        condition=self.raw_entry(d).fillna(False)&(d.volume>0)
        event=condition&~condition.shift(1,fill_value=False)
        d['enter_long']=event.astype(int)
        d.loc[event,'enter_tag']=self.family
        return d

    def populate_exit_trend(self,dataframe:DataFrame,metadata:dict)->DataFrame:
        d=dataframe.copy()
        if self.family=='trend': condition=d.close<d.ema50
        elif self.family=='breakout': condition=d.close<d.prior_low12
        elif self.family=='reversion': condition=(d.close>=d.ema20)|(d.rsi14>=50)
        elif self.family=='squeeze': condition=d.close<d.ema20
        elif self.family=='momentum': condition=(d.return24<=0)|(d.close<d.ema20)
        else: raise ValueError(self.family)
        d['exit_long']=(condition.fillna(False)&(d.volume>0)).astype(int)
        d.loc[d.exit_long.eq(1),'exit_tag']=self.family+'_exit'
        return d


class AlphaTrend(AlphaBase): family='trend'
class AlphaTrendLo(AlphaTrend): efficiency_min=.25
class AlphaTrendHi(AlphaTrend): efficiency_min=.35
class AlphaBreakout(AlphaBase): family='breakout'
class AlphaBreakoutLo(AlphaBreakout): breakout_window=20
class AlphaBreakoutHi(AlphaBreakout): breakout_window=28
class AlphaReversion(AlphaBase): family='reversion'
class AlphaReversionLo(AlphaReversion): stretch_atr=1.35
class AlphaReversionHi(AlphaReversion): stretch_atr=1.65
class AlphaSqueeze(AlphaBase): family='squeeze'
class AlphaSqueezeLo(AlphaSqueeze): keltner_multiplier=1.35
class AlphaSqueezeHi(AlphaSqueeze): keltner_multiplier=1.65
class AlphaMomentum(AlphaBase): family='momentum'
class AlphaMomentumLo(AlphaMomentum): persistence_min=.55
class AlphaMomentumHi(AlphaMomentum): persistence_min=.65

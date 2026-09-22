"""Fixed long-only SMA crossover benchmark; no AI or optimized parameters."""
from pandas import DataFrame
from freqtrade.strategy import IStrategy


class LabBaseline(IStrategy):
    INTERFACE_VERSION = 3
    timeframe = "1h"
    can_short = False
    startup_candle_count = 51
    process_only_new_candles = True
    minimal_roi = {"0": 0.05}
    stoploss = -0.05
    trailing_stop = False
    use_exit_signal = True
    exit_profit_only = False
    order_types = {
        "entry": "limit", "exit": "limit", "stoploss": "market",
        "stoploss_on_exchange": False,
    }
    order_time_in_force = {"entry": "GTC", "exit": "GTC"}

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["sma_fast"] = dataframe["close"].rolling(20).mean()
        dataframe["sma_slow"] = dataframe["close"].rolling(50).mean()
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["enter_long"] = 0
        crossed = (
            (dataframe["sma_fast"] > dataframe["sma_slow"])
            & (dataframe["sma_fast"].shift(1) <= dataframe["sma_slow"].shift(1))
            & (dataframe["volume"] > 0)
        )
        dataframe.loc[crossed, ["enter_long", "enter_tag"]] = (1, "sma_cross_up")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
        crossed = (
            (dataframe["sma_fast"] < dataframe["sma_slow"])
            & (dataframe["sma_fast"].shift(1) >= dataframe["sma_slow"].shift(1))
            & (dataframe["volume"] > 0)
        )
        dataframe.loc[crossed, ["exit_long", "exit_tag"]] = (1, "sma_cross_down")
        return dataframe

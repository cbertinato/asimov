import pandas as pd
import numpy as np

from .backtest import Strategy
from .prices import macd


class MACDCrossStrategy(Strategy):
    def __init__(self, symbol: str, bars: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9):
        self.symbol = symbol
        self.bars = bars
        self.fast = fast
        self.slow = slow
        self.signal = signal

    def generate_signals(self) -> pd.Series:
        df = macd(self.bars, slow=self.slow, fast=self.fast, signal=self.signal)
        return pd.Series(np.where(df['macd'] > df['signal'], 1, 0), index=df.index).diff().dropna()

        # find crossings
        # crossing = pd.Series(np.where(df['macd'] > df['signal'], 1, -1), index=df.index)
        # crossing = crossing.rolling(window=2).apply(lambda x: sum(x) == 0, raw=False).astype('bool')

        # df['divergence'] = np.abs(df['macd'] - df['signal'])
        # df['momentum'] = df['divergence'].diff()
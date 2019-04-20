import pandas as pd

from .backtest import Portfolio


class MarketOnClosePortfolio(Portfolio):

    def __init__(self, symbol: str, bars: pd.DataFrame, signals: pd.Series, initial_capital: float = 10000.0):
        self.symbol = symbol
        self.bars = bars
        self.signals = signals
        self.initial_capital = float(initial_capital)
        self.positions = self.generate_positions()

    def generate_positions(self) -> pd.DataFrame:
        positions = pd.DataFrame(index=self.signals.index).fillna(0)
        positions[self.symbol] = 100 * self.signals
        return positions

    def backtest(self) -> Portfolio:
        holdings = self.positions.rmul(self.bars['close'], axis=0)
        pos_diff = self.positions.diff()
        portfolio = pd.DataFrame(index=self.positions.index)
        portfolio['holdings'] = holdings.sum(axis=1)
        portfolio['cash'] = self.initial_capital - (pos_diff[self.symbol] * self.bars['close']).cumsum()
        portfolio['total'] = portfolio['holdings'] + portfolio['cash']
        portfolio['returns'] = portfolio['total'].pct_change()
        portfolio['cum_returns'] = (1 + portfolio['returns']).cumprod()
        portfolio['drawdown'] = 1 - portfolio['cum_returns'] / portfolio['cum_returns'].cummax()

        return portfolio

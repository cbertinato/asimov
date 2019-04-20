from abc import ABC, abstractmethod


class Strategy(ABC):

    @abstractmethod
    def generate_signals(self):
        """ Provides logic that determines buy/hold/sell signals {1, 0, -1}"""
        raise NotImplementedError('Strategy class must implement signals()')


class Portfolio(ABC):

    @abstractmethod
    def generate_positions(self):
        """ Provides logic to determine how positions are allocated """
        raise NotImplementedError('Portfolio class must implement positions()')

    @abstractmethod
    def backtest(self):
        """ Provides logic to generate trading orders and subsequent equity curve """
        raise NotImplementedError('Portfolio class must implement backtest()')

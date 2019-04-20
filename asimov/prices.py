import os
import requests
import json
import re
from dataclasses import dataclass, InitVar
from datetime import datetime
from typing import Tuple, Union

import pandas as pd
import numpy as np


# API_KEY = os.getenv('AV_API_KEY')
API_KEY = 'DSXYUZ8DGDH24QB3'
base_url = 'https://www.alphavantage.co/query'


def _string_map(columns):
    column_map = dict()
    for column in columns:
        new_column = column.split()
        column_map[column] = '_'.join([c.lower() for c in new_column[1:]])
    return column_map


def _rename_dict_keys(dictionary):
    column_map = _string_map(dictionary.keys())
    for item in dictionary.copy():
        dictionary[column_map[item]] = dictionary.pop(item)


def _fetch(*, symbol, function, interval=None, outputsize='compact'):
    if not API_KEY:
        raise Exception('No API key')

    payload = {'symbol': symbol, 'apikey': API_KEY, 'function': function}

    if interval is not None:
        payload['interval'] = interval

    if outputsize in ('compact', 'full'):
        payload['outputsize'] = outputsize
    else:
        raise ValueError(f'Invalid value for argument "outputsize": {outputsize}')

    response = requests.get(base_url, params=payload)

    if response.status_code != 200:
        raise Exception(f'Status code: {response.status_code}, Message: {response.content}')

    return response


def time_series_intraday(symbol: str, interval: str = '60min',
                         outputsize: str = 'compact') -> Tuple[pd.DataFrame, dict]:
    """ Intraday equity time series

    Retrieves intraday time series (timestamp, open, high, low, close, volume) of the equity specified
    up to the current time for the current or last trading day.

    Parameters
    ----------
    symbol : str
        Name of the equity.
    interval : {'1min', '5min', '15min', '30min', '60min'}, default '60min'
        Time interval between two consecutive data points in the time series.
    outputsize : {'compact', 'full'}, default 'compact'
        `compact` returns only the latest 100 data points in the intraday time series; `full` returns the
        full-length intraday time series. Default: `compact`

    Returns
    -------
        :obj:`DataFrame`, :obj:`dict`

    """
    response = _fetch(symbol=symbol, function='TIME_SERIES_INTRADAY', interval=interval,
                      outputsize=outputsize)

    response_dict = json.loads(response.content)

    df = pd.DataFrame.from_dict(response_dict[f'Time Series ({interval})'], orient='index', dtype=np.float64)
    df.index = pd.to_datetime(df.index)
    df = df.rename(columns=_string_map(df.columns))

    metadata = response_dict['Meta Data']
    _rename_dict_keys(metadata)

    metadata['begin_datetime'] = df.index.min()
    metadata['end_datetime'] = df.index.max()

    return df, metadata


def time_series_daily(symbol: str, outputsize: str = 'compact') -> Tuple[pd.DataFrame, dict]:
    """ Daily equity time series

    Retrieves daily time series (date, daily open, daily high, daily low, daily close, daily volume) of the equity
    specified up to the current time.

    Parameters
    ----------
    symbol : str
        Name of the equity.

    outputsize : {'compact', 'full'}, default 'compact'
        `compact` returns only the latest 100 data points; `full` returns the full-length time series of up to
        20 years of historical data.

    Returns
    -------
        :obj:`DataFrame`, :obj:`dict`

    """
    response = _fetch(symbol=symbol, function='TIME_SERIES_DAILY', outputsize=outputsize)

    response_dict = json.loads(response.content)

    df = pd.DataFrame.from_dict(response_dict[f'Time Series (Daily)'], orient='index', dtype=np.float64)
    df.index = pd.to_datetime(df.index)
    df = df.rename(columns=_string_map(df.columns))

    metadata = response_dict['Meta Data']
    _rename_dict_keys(metadata)

    metadata['begin_datetime'] = df.index.min()
    metadata['end_datetime'] = df.index.max()

    return df, metadata


def time_series_daily_adj(symbol: str, outputsize: str ='compact') -> Tuple[pd.DataFrame, dict]:
    """ Daily equity time series adjusted

    Retrieves daily time series (date, daily open, daily high, daily low, daily close, daily volume,
    daily adjusted close, and split/dividend events) of the equity specified up to the current time.

    Parameters
    ----------
    symbol : str
        Name of the equity.

    outputsize : {'compact', 'full'}, default 'compact'
        `compact` returns only the latest 100 data points; `full` returns the full-length time series of up to
        20 years of historical data.

    Returns
    -------
        :obj:`DataFrame`, :obj:`dict`

    """
    response = _fetch(symbol=symbol, function='TIME_SERIES_DAILY_ADJUSTED', outputsize=outputsize)

    response_dict = json.loads(response.content)

    df = pd.DataFrame.from_dict(response_dict[f'Time Series (Daily)'], orient='index', dtype=np.float64)
    df.index = pd.to_datetime(df.index)
    df = df.rename(columns=_string_map(df.columns))

    metadata = response_dict['Meta Data']
    _rename_dict_keys(metadata)

    metadata['begin_datetime'] = df.index.min()
    metadata['end_datetime'] = df.index.max()

    return df, metadata


def get_time_series(symbol: str, freq: str = '1D', begin: Union[str, datetime] = None,
                    end: Union[str, datetime] = None, adjusted: bool = False) -> pd.DataFrame:

    pattern = r'^(?P<qty>\d*)(?P<unit>[mHDWMQY])$'
    frequency = re.match(pattern, freq)

    if frequency is None:
        raise Exception(f'Invalid frequency string: {freq}')

    freq_qty = int(frequency.group('qty'))
    freq_unit = frequency.group('unit')
    if freq_unit == 'm' and freq_qty not in [1, 5, 15, 30, 60]:
        raise Exception(f'Invalid frequency string: {freq}')

    if isinstance(begin, str):
        begin_dt = datetime.strptime(begin, '%Y-%m-%d')
    else:
        begin_dt = begin

    if isinstance(end, str):
        end_dt = datetime.strptime(end, '%Y-%m-%d')
    else:
        end_dt = end

    if freq_unit == 'm':
        df, metadata = time_series_intraday(symbol, f'{freq_qty}min', outputsize='full')
        if df.index.min() > begin_dt:
            print(f'WARNING: Not all data is available back to the specified begin datetime: {begin_dt}. The earliest '
                  f'available datapoint is {df.index.min()}.')

    else:
        if begin_dt is None or (end_dt - begin_dt).days >= 100:
            outputsize = 'full'
        else:
            outputsize = 'compact'

        if adjusted:
            df, metadata = time_series_daily_adj(symbol, outputsize=outputsize)
        else:
            df, metadata = time_series_daily(symbol, outputsize=outputsize)

    df = df.loc[begin_dt:end_dt]
    return df


@dataclass
class Equity:
    symbol: str
    freq: str
    begin: InitVar[str]
    end: InitVar[str]
    time_series: pd.DataFrame = None

    def __post_init__(self, begin: str, end: str):
        self.time_series = get_time_series(self.symbol, freq=self.freq, begin=begin, end=end)

    def __repr__(self):
        return (f'{self.__class__.__name__}(symbol={self.symbol}, '
                f'freq={self.freq}, '
                f'begin={min(self.time_series.index)}, end={max(self.time_series.index)})')


def macd(ts: pd.DataFrame, slow: int = 26, fast: int = 12, signal: int = 9, percent=True) -> pd.DataFrame:
    if percent:
        returns = ts['close'].pct_change(1)
    else:
        returns = np.log(ts['close']).diff()

    a = returns.ewm(span=fast).mean()
    b = returns.ewm(span=slow).mean()
    mac = (a - b).dropna()
    sig = mac.ewm(span=signal).mean().dropna()

    df = pd.concat([mac, sig], axis=1)
    df.columns = ['macd', 'signal']

    return df

import os
import requests
import json
from dataclasses import dataclass
import pandas as pd


API_KEY = os.getenv('AV_API_KEY')
base_url = 'https://www.alphavantage.co/query'


@dataclass
class Equity:
    symbol: str
    time_series: pd.DataFrame
    interval: str
    metadata: dict

    def __repr__(self):
        return (f'{self.__class__.__name__}(symbol={self.symbol}, '
                f'interval={self.interval}, '
                f'begin_datetime={self.metadata["begin_datetime"]})')


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


def time_series_intraday(symbol: str, **kwargs) -> Equity:
    """ Intraday equity time series

    Retrieves intraday time series from Alpha Vantage up to the current time for the current or last trading day.

    Parameters
    ----------
    symbol : str
        Name of the equity.

    **kwargs:
        interval : {'1min', '5min', '15min', '30min', '60min'}, default '60min'
            Time interval between two consecutive data points in the time series.
        outputsize : {'compact', 'full'}, default 'compact'
            `compact` returns only the latest 100 data points in the intraday time series; `full` returns the
            full-length intraday time series. Default: `compact`

    Returns
    -------
        :obj:`Equity`

    """
    payload = {'symbol': symbol, 'apikey': API_KEY, 'function': 'TIME_SERIES_INTRADAY'}

    payload['interval'] = kwargs.get('interval', '60min')
    outputsize = kwargs.get('outputsize')

    if outputsize:
        if outputsize in ('compact', 'full'):
            payload['outputsize'] = kwargs['outputsize']
        else:
            raise ValueError(f'Invalid value for argument "outputsize": {outputsize}')

    response = requests.get(base_url, params=payload)

    if response.status_code != 200:
        raise Exception(f'Status code: {response.status_code}, Message: {response.content}')

    response_dict = json.loads(response.content)

    df = pd.DataFrame.from_dict(response_dict[f'Time Series ({payload["interval"]})'], orient='index')
    df.index = pd.to_datetime(df.index)
    df = df.rename(columns=_string_map(df.columns))

    metadata = response_dict['Meta Data']
    _rename_dict_keys(metadata)

    metadata['begin_datetime'] = df.index.min()
    metadata['end_datetime'] = df.index.max()

    return Equity(symbol=symbol, time_series=df, interval=f'intraday, {metadata["interval"]}', metadata=metadata)


def time_series_daily(symbol: str, **kwargs) -> Equity:
    """ Daily equity time series

    Retrieves daily time series from Alpha Vantage up to the current time.

    Parameters
    ----------
    symbol : str
        Name of the equity.

    **kwargs:
        interval : {'1min', '5min', '15min', '30min', '60min'}, default '60min'
            Time interval between two consecutive data points in the time series.
        outputsize : {'compact', 'full'}, default 'compact'
            `compact` returns only the latest 100 data points; `full` returns the full-length time series of up to
            20 years of historical data.

    Returns
    -------
        :obj:`Equity`

    """
    payload = {'symbol': symbol, 'apikey': API_KEY, 'function': 'TIME_SERIES_DAILY'}

    outputsize = kwargs.get('outputsize')

    if outputsize:
        if outputsize in ('compact', 'full'):
            payload['outputsize'] = kwargs['outputsize']
        else:
            raise ValueError(f'Invalid value for argument "outputsize": {outputsize}')

    response = requests.get(base_url, params=payload)

    if response.status_code != 200:
        raise Exception(f'Status code: {response.status_code}, Message: {response.content}')

    response_dict = json.loads(response.content)

    df = pd.DataFrame.from_dict(response_dict[f'Time Series (Daily)'], orient='index')
    df.index = pd.to_datetime(df.index)
    df = df.rename(columns=_string_map(df.columns))

    metadata = response_dict['Meta Data']
    _rename_dict_keys(metadata)

    metadata['begin_datetime'] = df.index.min()
    metadata['end_datetime'] = df.index.max()

    return Equity(symbol=symbol, time_series=df, interval='daily', metadata=metadata)
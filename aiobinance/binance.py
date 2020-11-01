import pandas as pd
from datetime import datetime

from .api import BinanceRaw
from .model.trades import Trades
from .model.ohlcv import OHLCV


def trades_from_binance() -> Trades:
    raise NotImplementedError
    return Trades()


def ohlcv_from_binance(startTime: int, endTime: int, symbol: str) -> OHLCV:
    api = BinanceRaw(API_KEY="", API_SECRET="")  # we dont need private requests here
    # Ref : https://binance-docs.github.io/apidocs/spot/en/#kline-candlestick-data

    interval = BinanceRaw.interval(startTime, endTime)

    res = api.call_api(command='klines', symbol=symbol, interval=interval, startTime=startTime, endTime=endTime,
                            limit=1000)

    # Ref : https://gist.github.com/ashwinimaurya/06728a31bcfb08209ef4fb13fd058163#file-binance_ohlc-py
    columns = ['open_time', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'qav', 'num_trades',
               'taker_base_vol',
               'taker_quote_vol', 'is_best_match']
    df = pd.DataFrame(data=res, columns=columns)

    df.open_time = pd.to_datetime(df.open_time, unit='ms')
    df.close_time = pd.to_datetime(df.close_time, unit='ms')
    return OHLCV(df)

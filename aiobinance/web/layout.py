from datetime import datetime

import bokeh.layouts

from aiobinance import binance
from aiobinance.model import OHLCV, TradeFrame

from ..config import load_api_keyfile
from .pnl_plot import pnl_plot
from .price_plot import price_plot


def symbol_layout(symbol: str, from_datetime: datetime, to_datetime: datetime):

    # TODO : compute interval...

    ohlcv = binance.price_from_binance(
        start_time=from_datetime,
        end_time=to_datetime,
        symbol=symbol,
    )

    # TMP : TODO get it from "higher level context" like binance client code...
    creds = load_api_keyfile()

    trades = binance.trades_from_binance(
        symbol=symbol,
        start_time=from_datetime,
        end_time=to_datetime,
        credentials=creds,
    )

    price = price_plot(ohlcv, trades=trades)

    if trades and len(trades) > 0:
        pnl = pnl_plot(trades=trades)

        return bokeh.layouts.grid([pnl, price])
    else:
        return bokeh.layouts.grid([price])


def trades_layout(ohlcv: OHLCV, trades: TradeFrame):

    pnl = pnl_plot(trades=trades)
    price = price_plot(ohlcv, trades=trades)

    return bokeh.layouts.grid([pnl, price])

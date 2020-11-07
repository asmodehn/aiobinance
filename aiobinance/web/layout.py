import bokeh.layouts

from aiobinance.model import OHLCV, TradeFrame

from . import pnl_plot, price_plot


def trades_layout(ohlcv: OHLCV, trades: TradeFrame):

    pnl = pnl_plot(trades=trades)
    price = price_plot(ohlcv, trades=trades)

    return bokeh.layouts.grid([pnl, price])

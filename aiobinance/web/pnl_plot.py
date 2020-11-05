import pandas as pd
import numpy as np

from ..model import Trades

from bokeh.models import ColumnDataSource
from bokeh.plotting import Figure, figure


def pnl_plot(trades: Trades, cumulative=True) -> Figure:
    tools = "pan,wheel_zoom,xbox_select,reset"

    # Note: amount is in BASE currency. but usually we are interested in PnL in QUOTE currency
    # SELL is positive (increase QUOTE wallet)
    # BUY is negative (decrease QUOTE wallet)
    tradeamount = trades["Amount"] * np.where(trades["Trade"] == "SELL", 1, -1)
    # print(tradeamount)

    tradeval = trades["Price"] * tradeamount
    # print(tradeval.cumsum())

    plotdata = pd.DataFrame(
        data={
            "timestamp": trades["datetime"],
            "plotted": tradeval.cumsum() if cumulative else tradeval,
        }
    )

    source = ColumnDataSource(data=plotdata)

    pnl = figure(plot_width=720, plot_height=350, x_axis_type="datetime", tools=tools)

    pnl.line(x="timestamp", y="plotted", source=source)

    return pnl

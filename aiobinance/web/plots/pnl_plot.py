import numpy as np
import pandas as pd
from bokeh.models import ColumnDataSource
from bokeh.plotting import Figure, figure

from ...api.tradesview import TradesView


def pnl_plot(trades: TradesView, cumulative=True) -> Figure:
    tools = "pan,wheel_zoom,xbox_select,reset"

    trades_df = trades.frame.optimized()

    # Note: amount is in BASE currency. but usually we are interested in PnL in QUOTE currency
    # SELL is positive (increase QUOTE wallet)
    # BUY is negative (decrease QUOTE wallet)
    tradeamount = trades_df.qty * np.where(trades_df.is_buyer, -1, 1)
    # print(tradeamount)

    tradeval = trades_df.price * tradeamount
    # print(tradeval.cumsum())

    plotdata = pd.DataFrame(
        data={
            "timestamp": trades_df.time,
            "plotted": tradeval.cumsum() if cumulative else tradeval,
        }
    )

    source = ColumnDataSource(data=plotdata)

    pnl = figure(plot_width=720, plot_height=350, x_axis_type="datetime", tools=tools)

    pnl.line(x="timestamp", y="plotted", source=source)

    return pnl

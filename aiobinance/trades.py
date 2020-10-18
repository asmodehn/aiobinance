import numpy as np

from bokeh.models import ColumnDataSource
from bokeh.plotting import Figure, figure, show
from bokeh.io import output_notebook

output_notebook()

import pandas as pd

class Trades:
    trades: pd.DataFrame

    def __init__(self, csv_filepath: str):
        # CSV is produced by hummingbot v0.30.0
        self.trades = pd.read_csv(csv_filepath,
                     usecols=[
        "Timestamp",
        "Base",
        "Quote",
        "Trade",
        "Type",
        "Price",
        "Amount",
        "Fee",
        "Age",
        "Order ID"
    ])

    def head(self):
        return self.trades.head()

    def pnl_plot(self, cumulative=True) -> Figure:

        tools = 'pan,wheel_zoom,xbox_select,reset'

        # Note: amount is in BASE currency. but usually we are interested in PnL in QUOTE currency
        # SELL is positive (increase QUOTE wallet)
        # BUY is negative (decrease QUOTE wallet)
        tradeamount = self.trades['Amount'] * np.where(self.trades['Trade'] == 'SELL', 1, -1)
        # print(tradeamount)

        tradeval = self.trades['Price'] * tradeamount
        # print(tradeval.cumsum())

        self.trades['datetime'] = pd.to_datetime(self.trades.Timestamp, unit='ms')

        plotdata = pd.DataFrame(data={
            'timestamp': self.trades.datetime,
            'plotted': tradeval.cumsum() if cumulative else tradeval
        })

        source = ColumnDataSource(data=plotdata)

        pnl = figure(plot_width=720, plot_height=350,
                        x_axis_type ='datetime',
                      tools=tools)

        pnl.line(x='timestamp', y='plotted', source=source)

        return pnl

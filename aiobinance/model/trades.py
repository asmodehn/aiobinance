import numpy as np

from bokeh.models import ColumnDataSource
from bokeh.plotting import Figure, figure, show
from bokeh.io import output_notebook

output_notebook()

import pandas as pd

class Trades:
    trades: pd.DataFrame

    def __init__(self, trades: pd.DataFrame):
        # CSV is produced by hummingbot v0.30.0
        self.trades = trades  # TODO : strong type check of trades (shape of df, etc.)

        # adding a "standard" datetime column (should we get rid of timestamp to not duplicate data ?)
        self.trades['datetime'] = pd.to_datetime(self.trades.Timestamp, unit='ms')

    ### DF interface
    def head(self):
        return self.trades.head()

    @property
    def Timestamp(self):
        # we dont want to allow all dataframe attributes access.
        # only whats necessary from the outside to determine a clean interface...
        return self.trades.Timestamp

    @property
    def loc(self):
        return self.trades.loc

    def __getitem__(self, item):
        return self.trades[item]

    # NO SETTING ON TRADES :they are immutable events.
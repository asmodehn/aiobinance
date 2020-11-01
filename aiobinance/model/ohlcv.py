import pandas as pd

from bokeh.models import BooleanFilter, CDSView, ColumnDataSource, Legend
from bokeh.plotting import Figure


class OHLCV:

    df: pd.DataFrame

    def __init__(self, ohlcv: pd.DataFrame):
        self.df = ohlcv  # TODO : strong type check of df (shape, columns, etc.)

    def head(self):
        return self.df.head()

    @property
    def Timestamp(self):
        # we don't want to allow all dataframe attributes access.
        # only whats necessary from the outside to determine a clean interface...
        return self.df.Timestamp

    @property
    def loc(self):
        return self.df.loc

    def __getitem__(self, item):
        return self.df[item]

    # Is this a good idea ? or should we keep it immutable ??
    # cf mid_time computation in plot...
    def __setitem__(self, key, value):
        self.df[key] = value

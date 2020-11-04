from decimal import Decimal

import pandas as pd

from bokeh.models import BooleanFilter, CDSView, ColumnDataSource, Legend
from bokeh.plotting import Figure


from datetime import datetime
from typing import List, Optional

from pydantic import validator
from pydantic.dataclasses import dataclass
from dataclasses import asdict


# Leveraging pydantic to validate based on type hints
@dataclass
class Candle:
    # REMINDER : as 'precise' and 'pythonic' semantic as possible
    open_time: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    close_time: datetime
    qav: Decimal
    num_trades: int
    taker_base_vol: Decimal
    taker_quote_vol: Decimal
    is_best_match: int  # ??

    @validator('open_time', 'close_time', pre=True)
    def convert_pandas_timestamp(cls, v):
        if isinstance(v, pd.Timestamp):
            return v.to_pydatetime()
        return v


class OHLCV:

    _df: pd.DataFrame

    def __init__(self, *candles: Candle):
        # Here we follow binance format and enforce proper python types

        df = pd.DataFrame.from_records([asdict(dc) for dc in candles])

        self._df = df

    def __getitem__(self, item: int):  # TODO : slice
        if item < len(self._df):
            return Candle(**self._df.iloc[item])
        elif self._df.open_time[0] < item < self._df.close_time[-1]:
            return Candle(**self._df[self._df.id == item])
        else:
            raise KeyError(f"No Candle with index {item} or containing time {item}")

    # Is this a good idea ? or should we keep it immutable ??
    # cf mid_time computation in plot...
    def __setitem__(self, key, value):
        self._df[key] = value

    def __iter__(self):
        return (Candle(**t._asdict()) for t in self._df.itertuples(index=False))

    def __len__(self):
        return len(self._df)

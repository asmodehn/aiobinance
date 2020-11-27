from dataclasses import asdict, fields
from datetime import datetime
from decimal import Decimal
from typing import Iterable, List, Optional

import hypothesis.strategies as st
import pandas as pd
from bokeh.models import BooleanFilter, CDSView, ColumnDataSource, Legend
from bokeh.plotting import Figure
from pydantic import validator
from pydantic.dataclasses import dataclass


# Leveraging pydantic to validate based on type hints
@dataclass
class Ticker:
    # REMINDER : as 'precise' and 'pythonic' semantic as possible
    symbol: str
    price_change: Decimal
    price_change_percent: Decimal
    weighted_avg_price: Decimal
    prev_close_price: Decimal
    last_price: Decimal
    last_qty: Decimal
    bid_price: Decimal
    ask_price: Decimal
    open_price: Decimal
    high_price: Decimal
    low_price: Decimal
    volume: Decimal
    quote_volume: Decimal
    open_time: datetime
    close_time: datetime
    first_id: int  # First tradeId
    last_id: int  # Last tradeId
    count: int  # Trade count

    @validator("open_time", "close_time", pre=True)
    def convert_pandas_timestamp(cls, v):
        if isinstance(v, pd.Timestamp):
            return v.to_pydatetime()
        return v

    def __str__(self):
        return f"""
symbol: {self.symbol}
price_change: {self.price_change}
price_change_percent: {self.price_change_percent}
weighted_avg_price: {self.weighted_avg_price}
prev_close_price: {self.prev_close_price}
last_price: {self.last_price}
last_qty: {self.last_qty}
bid_price: {self.bid_price}
ask_price: {self.ask_price}
open_price: {self.open_price}
high_price: {self.high_price}
low_price: {self.low_price}
volume: {self.volume}
quote_volume: {self.quote_volume}
open_time: {self.open_time}
close_time: {self.close_time}
first_id: {self.first_id}
last_id: {self.last_id}
count: {self.count}
"""

    def __dir__(self) -> Iterable[str]:
        return [f.name for f in fields(self)]


# Strategies, inferring attributes from type hints by default
def st_ticker():
    return st.builds(
        Ticker,
        price_change=st.decimals(allow_nan=False, allow_infinity=False),
        price_change_percent=st.decimals(allow_nan=False, allow_infinity=False),
        weighted_avg_price=st.decimals(allow_nan=False, allow_infinity=False),
        prev_close_price=st.decimals(allow_nan=False, allow_infinity=False),
        last_price=st.decimals(allow_nan=False, allow_infinity=False),
        last_qty=st.decimals(allow_nan=False, allow_infinity=False),
        bid_price=st.decimals(allow_nan=False, allow_infinity=False),
        ask_price=st.decimals(allow_nan=False, allow_infinity=False),
        open_price=st.decimals(allow_nan=False, allow_infinity=False),
        high_price=st.decimals(allow_nan=False, allow_infinity=False),
        low_price=st.decimals(allow_nan=False, allow_infinity=False),
        volume=st.decimals(allow_nan=False, allow_infinity=False),
        quote_volume=st.decimals(allow_nan=False, allow_infinity=False),
    )

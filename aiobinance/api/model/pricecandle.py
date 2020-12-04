from __future__ import annotations

from dataclasses import asdict, fields
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Iterable, List, Optional

import hypothesis.strategies as st
import pandas as pd
from bokeh.models import BooleanFilter, CDSView, ColumnDataSource, Legend
from bokeh.plotting import Figure
from hypothesis import infer
from pydantic import validator
from pydantic.dataclasses import dataclass

# Leveraging pydantic to validate based on type hints
from tabulate import tabulate


@dataclass
class PriceCandle:
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

    @validator("open_time", "close_time", pre=True)
    def convert_pandas_timestamp(cls, v):
        if isinstance(v, pd.Timestamp):
            return v.to_pydatetime()
        return v

    # Strategies, inferring attributes from type hints by default
    @st.composite
    @staticmethod
    def strategy(draw, tf: Optional[timedelta] = None):
        ot = draw(st.datetimes())
        ct = draw(st.datetimes(min_value=ot)) if tf is None else ot + tf
        return PriceCandle(
            open_time=ot,
            open=draw(st.decimals(allow_nan=False, allow_infinity=False)),
            high=draw(st.decimals(allow_nan=False, allow_infinity=False)),
            low=draw(st.decimals(allow_nan=False, allow_infinity=False)),
            close=draw(st.decimals(allow_nan=False, allow_infinity=False)),
            volume=draw(st.decimals(allow_nan=False, allow_infinity=False)),
            close_time=ct,
            qav=draw(st.decimals(allow_nan=False, allow_infinity=False)),
            num_trades=draw(st.integers()),
            taker_base_vol=draw(st.decimals(allow_nan=False, allow_infinity=False)),
            taker_quote_vol=draw(st.decimals(allow_nan=False, allow_infinity=False)),
            is_best_match=draw(st.integers()),
        )

    def __str__(self) -> str:
        return f"""
open_time: {self.open_time}
open: {self.open}
high: {self.high}
low: {self.low}
close: {self.close}
volume: {self.volume}
close_time: {self.close_time}
qav: {self.qav}
num_trades: {self.num_trades}
taker_base_vol: {self.taker_base_vol}
taker_quote_vol: {self.taker_quote_vol}
is_best_match: {self.is_best_match}
"""

    def __dir__(self) -> Iterable[str]:
        # hiding private methods and data validators
        return [f.name for f in fields(self)]


if __name__ == "__main__":
    print(PriceCandle.strategy().example())

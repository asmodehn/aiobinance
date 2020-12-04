from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields
from datetime import datetime
from decimal import Decimal
from typing import Iterable, List, Optional, Union

import hypothesis.strategies as st
import pandas as pd
from bokeh.models import BooleanFilter, CDSView, ColumnDataSource, Legend
from bokeh.plotting import Figure
from hypothesis import infer
from pydantic import validator

# Leveraging pydantic to validate based on type hints
from tabulate import tabulate

from aiobinance.api.model.pricecandle import PriceCandle


# Note : these are python dataclasses as pydantic cannot really typecheck dataframe content...
@dataclass(frozen=True)
class OHLCFrame:

    df: Optional[pd.DataFrame] = field(
        init=True,
        default=pd.DataFrame.from_records(
            [], columns=[f.name for f in fields(PriceCandle)]
        ),
    )
    #
    # @property
    # def open_time(self) -> List[datetime]:
    #     return self.df.open_time.to_list()
    #
    # @property
    # def close_time(self) -> List[datetime]:
    #     return self.df.close_time.to_list()

    @st.composite
    @staticmethod
    def strategy(draw, max_size=5):
        tl = st.lists(
            elements=PriceCandle.strategy(),
            max_size=max_size,
            unique_by=lambda t: t.open_time,
        )
        # TODO : sort candles...
        return OHLCFrame.from_candleslist(*draw(tl))

    @classmethod
    def from_candleslist(cls, *candles: PriceCandle):

        df = pd.DataFrame.from_records(
            [asdict(dc) for dc in candles],
            columns=[f.name for f in fields(PriceCandle)],
        )
        return cls(df=df)

    def as_datasource(self, compute_mid_time=True) -> ColumnDataSource:
        plotdf = self.optimized()
        if compute_mid_time:
            timeinterval = plotdf.open_time[1] - plotdf.open_time[0]
            plotdf["mid_time"] = plotdf.open_time + timeinterval / 2

        return ColumnDataSource(plotdf)

    def __post_init__(self):
        # Here we follow binance format and enforce proper python types
        # TODO : assert proper dataframe format of columns...
        pass

    def __contains__(self, item: PriceCandle):
        for t in self:  # iterates and cast to Trade
            if t == item:  # using Trade equality
                return True
        return False

    def __eq__(self, other: OHLCFrame) -> bool:
        assert isinstance(
            other, OHLCFrame
        )  # in our design the type infers the columns.
        if self is other:
            # here we follow python on equality https://docs.python.org/3.6/reference/expressions.html#id12
            return True
        elif len(self) == len(other):
            # BEWARE : https://github.com/pandas-dev/pandas/issues/20442
            for s, o in zip(self, other):  # this iterates and cast to Trade
                if s != o:  # here we use Trade.__eq__ !
                    break
            else:
                return True
        else:
            return False

    def __getitem__(self, item: Union[int, slice]):
        # in frozen tradeframe, index is equivalent to iloc in dataframe : position in the sequence

        if isinstance(item, slice):
            # dataframe slice handled by pandas for simplicity
            tf = OHLCFrame(df=self.df[item])
            return tf

        elif isinstance(item, int):
            try:
                return PriceCandle(**self.df.iloc[item])
            except IndexError as ie:
                raise KeyError("TradeFrame index out of range") from ie
        else:
            raise KeyError(f"Invalid index {item}")

    # def __getitem__(self, item: int):
    #
    #     if isinstance(item, slice):
    #         assert item.step is None
    #         start = 0 if item.start is None else item.start
    #         stop = len(self) if item.stop is None else item.stop
    #
    #         if stop <= 0 or start >= len(self) or start >= stop:
    #             return EmptyOHLCV  # returns the empty immutable tradeframe.
    #
    #         if start <= 0 and stop >= len(self):
    #             return self  # whole slice returns the exact same instance, avoiding duplication.
    #
    #         # step is always 1 here, we do not want to skip anything or aggregate trades
    #         subtrades = []
    #         for t in self.df.itertuples(index=True):
    #             if start <= t.Index < stop:
    #                 td = {f: v for f, v in t._asdict().items() if f != "Index"}
    #                 subtrades.append(PriceCandle(**td))
    #             if stop is not None and t.Index > stop:
    #                 break  # early break after stop
    #         return OHLCFrame(*subtrades)
    #
    #     elif isinstance(item, int):
    #         if item < len(self.df):
    #             return PriceCandle(**self.df.iloc[item])
    #         elif self.df.open_time[0] < item < self.df.close_time[-1]:
    #             return PriceCandle(**self.df[self.df.id == item])
    #         else:
    #             KeyError(f"No Candle with index {item} or containing time {item}")
    #
    #     else:
    #         raise KeyError(f"Invalid index {item}")

    # Is this a good idea ? or should we keep it immutable ??
    # cf mid_time computation in plot...
    # TODO : make it disappear...
    def __setitem__(self, key, value):
        self.df[key] = value

    def __iter__(self):
        for t in self.df.itertuples(index=False):
            yield PriceCandle(**t._asdict())

    def __len__(self):
        return len(self.df)

    def __str__(self):
        # optimize before display (high decimal precision is not manageable by humans)
        optdf = self.optimized()
        return tabulate(optdf, headers="keys", tablefmt="psql")

    def optimized(self) -> pd.DataFrame:
        opt_copy = self.df.copy(deep=True)
        opt_copy.convert_dtypes()
        return opt_copy

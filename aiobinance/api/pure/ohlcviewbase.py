from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields
from datetime import datetime
from decimal import Decimal
from typing import Iterable, List, Optional, Union

import hypothesis.strategies as st
import pandas as pd
from bokeh.models import BooleanFilter, CDSView, ColumnDataSource, Legend
from bokeh.plotting import Figure
from cached_property import cached_property
from hypothesis import infer
from pandas import IntervalIndex
from pandas._libs.tslibs.np_datetime import OutOfBoundsDatetime
from pydantic import validator

# Leveraging pydantic to validate based on type hints
from tabulate import tabulate

from aiobinance.api.model.ohlcframe import OHLCFrame
from aiobinance.api.model.pricecandle import PriceCandle


# Note : these are python dataclasses as pydantic cannot really typecheck dataframe content...
@dataclass(frozen=False)
class OHLCViewBase:

    frame: Optional[OHLCFrame] = field(init=True, default=OHLCFrame())

    # properties like those of a PriceCandle
    # for list of column value in the frame, access directly the frame attribute
    @cached_property
    def open_time(self) -> Optional[datetime]:
        return self.frame.open_time[0] if self.frame else None

    @cached_property
    def close_time(self) -> Optional[datetime]:
        return self.frame.close_time[-1] if self.frame else None

    @staticmethod
    def strategy(max_size=5):
        return st.builds(OHLCViewBase, frame=OHLCFrame.strategy(max_size=max_size))

    @classmethod
    def from_candles(cls, *candles: PriceCandle):
        return cls(frame=OHLCFrame.from_candleslist(*candles))

    def __post_init__(self):
        # Here we follow binance format and enforce proper python types
        # TODO : assert proper dataframe format of columns...
        # setting open_time as index and ordering (required for slicing !)
        self.frame = OHLCFrame(
            df=self.frame.df.set_index("open_time", drop=False).sort_index()
        )

    def as_datasource(self, compute_mid_time=True) -> ColumnDataSource:
        plotdf = self.frame.optimized()
        if compute_mid_time:
            timeinterval = plotdf.open_time[1] - plotdf.open_time[0]
            plotdf["mid_time"] = plotdf.open_time + timeinterval / 2
        # TODO : live bokeh updates ??
        return ColumnDataSource(plotdf)

    def __call__(self, *, frame: Optional[OHLCFrame] = None, **kwargs) -> OHLCViewBase:
        """ self updating the instance with new dataframe..."""
        # return same instance if no change
        if frame is None:
            return self

        popping = []
        if self.frame is None:
            # because we may have cached invalid values from initialization (self.frame was None)
            popping.append("open_time")
            popping.append("close_time")
        else:  # otherwise we detect change leveraging pandas
            if self.frame.open_time != frame.open_time:
                popping.append(
                    "open_time"
                )  # because open_time only depends on open_time
            if self.frame.close_time != frame.close_time:
                popping.append(
                    "close_time"
                )  # because close_time only depends on close_time

        # updating by updating data
        self.frame = frame

        # and invalidating related caches
        for p in popping:
            self.__dict__.pop(p, None)

        # returning self to allow chaining
        return self

    def __contains__(self, item: Union[PriceCandle, datetime]) -> bool:
        # https://docs.python.org/2/reference/datamodel.html#object.__contains__
        if isinstance(item, PriceCandle):
            return item in self.frame
        elif isinstance(item, datetime) and self.frame:  # continuous index
            return self.frame.open_time[0] <= item < self.frame.close_time[-1]
        else:
            return False

    def __eq__(self, other: OHLCViewBase) -> bool:
        assert isinstance(
            other, OHLCViewBase
        )  # in our design the type infers the columns.
        if self is other:
            # here we follow python on equality https://docs.python.org/3.6/reference/expressions.html#id12
            return True
        else:  # delegate equality to the unique member: frame
            return self.frame == other.frame

    def __getitem__(
        self, item: Union[datetime, slice]
    ) -> Union[OHLCViewBase, PriceCandle]:
        if isinstance(item, slice):
            # dataframe slice handled by pandas boolean indexer
            try:
                tf = OHLCFrame(
                    df=self.frame.df.loc[item]
                )  # simple since dataframe is indexed on datetime
                return OHLCViewBase(frame=tf)
            except TypeError as te:
                raise KeyError(
                    f"{item} is too high a value for PriceCandle.open_time "
                ) from te
        elif isinstance(item, datetime):
            try:
                rs = self.frame.df.loc[
                    (self.frame.df.open_time <= item)
                    & (item < self.frame.df.close_time)
                ]
                # This implies index unicity and non-overlapping of time intervals...
                if len(rs) == 1:
                    return PriceCandle(
                        **rs.iloc[0]
                    )  # simple since dataframe is  indexed on id
                elif len(rs) == 0:
                    raise KeyError(f"Invalid index {item}")
                else:
                    raise KeyError(f"ERROR: Multiple PriceCandle matching {item} !!!")

            except OutOfBoundsDatetime as oobd:
                # TODO : handle/prevent overflow error when int is too large to be optimized by pandas/numpy
                # E   OverflowError: Python int too large to convert to C long
                # pandas/_libs/hashtable_class_helper.pxi:1032: OverflowError
                raise KeyError(f"{item} out of bounds ") from oobd
            except IndexError as ie:
                raise KeyError(f"No PriceCandle.open_time matching {item}") from ie
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
        self.frame.df[key] = value

    # NO SETTING ON OHLCFrame if possible...
    # but new columns could be added on the fly, if computed from existing data...

    def __iter__(self):
        yield from self.frame

    # TODO : aiter

    def __len__(self):
        return len(self.frame)

    def __str__(self):
        return str(self.frame)


if __name__ == "__main__":

    print(OHLCViewBase.strategy().example())

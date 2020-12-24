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


class OHLCViewBase:

    frame: Optional[OHLCFrame]

    # properties like those of a PriceCandle
    # for list of column value in the frame, access directly the frame attribute
    @property
    def open_time(self) -> Optional[datetime]:
        return self.frame.open_time if self.frame else None

    @property
    def close_time(self) -> Optional[datetime]:
        return self.frame.close_time if self.frame else None

    @staticmethod
    def strategy(max_size=5):
        return st.builds(OHLCViewBase, frame=OHLCFrame.strategy(max_size=max_size))

    def __init__(self, frame: OHLCFrame = OHLCFrame()):
        self.frame = frame

    def __call__(self, *, frame: Optional[OHLCFrame] = None, **kwargs) -> OHLCViewBase:
        """ self updating the instance with new dataframe..."""
        # return same instance if no change
        if frame is None:
            return self

        popping = []
        if self.frame is None:
            # because we may have cached invalid values from initialization (self.frame was None)
            # popping.append("open_time")
            pass
        else:  # otherwise we detect change leveraging pandas
            # if self.frame.open_time != frame.open_time:
            #     popping.append(
            #         "open_time"
            #     )  # because open_time only depends on open_time
            pass

        # updating by updating data
        self.frame = frame

        # and invalidating related caches
        for p in popping:
            self.__dict__.pop(p, None)

        # returning self to allow chaining
        return self

    # Exposing mapping interface on continuous time index
    # We are entirely relying on OHLCFrame here

    def __contains__(self, item: Union[PriceCandle, datetime]) -> bool:
        # https://docs.python.org/2/reference/datamodel.html#object.__contains__
        return item in self.frame

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
        res = self.frame[item]
        if isinstance(res, OHLCFrame):
            return OHLCViewBase(frame=res)
        else:
            return res

    def __iter__(self):
        yield from self.frame

    # TODO : aiter

    def __len__(self):
        return len(self.frame)

    # These could be specialized for this interactive class...
    def __repr__(self):
        return repr(self.frame)

    def __str__(self):
        return str(self.frame)


if __name__ == "__main__":

    print(OHLCViewBase.strategy().filter(lambda v: len(v) > 0).example())

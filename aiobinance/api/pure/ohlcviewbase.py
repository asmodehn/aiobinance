from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Iterable, List, Optional, Union

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
from aiobinance.api.model.timeinterval import TimeInterval, TimeStep


class OHLCViewBase:
    frames: Dict[TimeStep, Optional[OHLCFrame]]

    # properties like those of a PriceCandle
    # for list of column value in the frame, access directly the frame attribute
    @property
    def open_time(self) -> Optional[datetime]:
        return min(f.open_time for f in self.frames.values()) if self.frames else None

    @property
    def close_time(self) -> Optional[datetime]:
        return min(f.close_time for f in self.frames.values()) if self.frames else None

    @property
    def interval(self) -> Optional[List[timedelta]]:  # TODO : timedelta or TimeStep ?
        return [tf.delta.value for tf in self.frames.keys()]

    @st.composite
    @staticmethod
    def strategy(draw, max_size=5):
        frames = draw(st.lists(OHLCFrame.strategy(), max_size=max_size))
        return OHLCViewBase(*frames)

    def __init__(self, *frames: OHLCFrame):
        self.frames = {}
        for f in frames:
            # default to minutely when unknown
            tstep = TimeStep(timedelta(minutes=1)) if f.interval is None else f.interval
            if tstep in self.frames:
                self.frames[tstep] = self.frames[tstep].union(f)  # merging frame
            else:
                self.frames[tstep] = f  # adding frame to the mapping

    def __call__(self, *, frame: Optional[OHLCFrame] = None, **kwargs) -> OHLCViewBase:
        """ self updating the instance with new dataframe, one frame at a time..."""
        # return same instance if no change
        if (
            frame is None or frame.empty
        ):  # Note : we cannot extract interval from an empty frame !
            return self

        # TODO: this should probably be encoded in frame types somehow, to avoid any mistakes when operating on them...
        tstep: TimeStep = frame.interval
        if tstep in self.frames.keys():
            self.frames[tstep] = self.frames[tstep].union(frame)
        else:  # if interval is unknown, we store the new frame.
            self.frames[tstep] = frame

        # returning self to allow chaining
        return self

    # Exposing mapping interface on interval ! (user is expected to access a frame if frame operation is required)
    def __contains__(self, item: Union[timedelta, TimeStep]) -> bool:
        # https://docs.python.org/2/reference/datamodel.html#object.__contains__
        if isinstance(item, timedelta):
            # convert to TimeStep
            item = TimeStep(item)
        return item in self.frames.keys()

    def __eq__(self, other: OHLCViewBase) -> bool:
        assert isinstance(
            other, OHLCViewBase
        )  # in our design the type infers the columns.
        if self is other:
            # here we follow python on equality https://docs.python.org/3.6/reference/expressions.html#id12
            return True
        else:  # delegate equality to the dict of frames
            return self.frames == other.frames

    def __getitem__(  # TODO : for simple thing, user can always access frame. BUT here we should manage timesteps...
        self, item: Union[list, timedelta, TimeStep, slice]
    ) -> Union[OHLCViewBase, OHLCFrame]:

        # Multi select returns a Narrowed view
        if isinstance(item, list):
            # For each item in the list we recurse
            return OHLCViewBase(*(self[el] for el in item))

        if isinstance(item, timedelta):  # for usability only.
            item = TimeStep(item)

        if isinstance(item, TimeStep):  # the simplest case
            if item not in self.frames:
                self.frames[
                    item
                ] = OHLCFrame()  # if not there, we just create a new empty one.
                # we expect a __call__() will fill it up with data later on.
            return self.frames[item]

        # Might return a view or a Frame
        if isinstance(item, slice):
            if item.step is None:  # pick them all
                return OHLCViewBase(
                    *(self.frames[tf][item.start : item.stop] for tf in self.frames)
                )
            else:  # recurse to interpret step properly and return the sliced frame
                return self[item.step][item.start : item.stop]

        raise RuntimeError(
            f"__getitem__ call on OHLCViewBase with {item} not understood... TimeStep expected."
        )

    def items(self):
        return self.frames.items()

    def keys(self):
        return self.frames.keys()

    def values(self):
        return self.frames.values()

    def __iter__(self):
        # default for a dict : iterating on keys
        return iter(self.keys())

    def __len__(self):
        return len(self.frames)

    # These could be specialized for this interactive class...
    def __repr__(self):
        return repr(self.frames)

    def __str__(self):
        return str(self.frames)


if __name__ == "__main__":

    print(OHLCViewBase.strategy().filter(lambda v: len(v) > 0).example())

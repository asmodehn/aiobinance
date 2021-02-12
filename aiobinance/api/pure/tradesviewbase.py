from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields
from datetime import datetime
from decimal import Decimal, getcontext
from typing import Iterable, List, Optional, Union

import hypothesis.strategies as st
import numpy as np
import pandas as pd
from bokeh.models import ColumnDataSource
from hypothesis.strategies import composite
from tabulate import tabulate

from aiobinance.api.model.order import OrderSide
from aiobinance.api.model.trade import Trade

# Note : these are python dataclasses as pydantic cannot really typecheck dataframe content...
from aiobinance.api.model.tradeframe import TradeFrame


class TradesViewBase:

    symbol: str
    frame: Optional[TradeFrame]

    @property
    def id(self) -> List[int]:
        if self.frame:
            return self.frame.id
        else:
            return []

    @st.composite
    @staticmethod
    def strategy(draw, max_size=5):
        symbol = draw(st.text(min_size=1, max_size=8))
        return (
            TradesViewBase(  # TODO : link symbol functionally (map, filter, flatmap.)
                symbol=symbol,
                frame=draw(
                    TradeFrame.strategy(symbols=st.just(symbol), max_size=max_size)
                ),
            )
        )

    def __init__(self, symbol: str, frame: Optional[TradeFrame] = None):
        self.symbol = symbol
        if frame is not None:
            assert frame.symbol == self.symbol
            self.frame = frame
        else:
            self.frame = TradeFrame(symbol=symbol)

    def __call__(
        self, *, frame: Optional[TradeFrame] = None, **kwargs
    ) -> TradesViewBase:
        """ self updating the instance with new dataframe..."""
        # return same instance if no change
        if frame is None:
            return self

        assert frame.symbol == self.symbol

        # updating by updating data
        self.frame = self.frame.union(frame)

        # returning self to allow chaining
        return self

    # Exposing mapping interface on continuous time index
    # We are entirely relying on TradeFrame here

    def __contains__(self, item: Union[Trade, int, datetime]) -> bool:
        # https://docs.python.org/2/reference/datamodel.html#object.__contains__
        return item in self.frame

    def __eq__(self, other: TradesViewBase) -> bool:
        assert isinstance(
            other, TradesViewBase
        )  # in our design the type infers the columns.
        assert self.symbol == other.symbol

        if self is other:
            # here we follow python on equality https://docs.python.org/3.6/reference/expressions.html#id12
            return True
        else:  # delegate equality to the unique member: frame
            return self.frame == other.frame

    def __getitem__(
        self, item: Union[int, datetime, slice]
    ) -> Union[TradesViewBase, Trade]:
        res = self.frame[item]
        if isinstance(res, TradeFrame):
            return TradesViewBase(symbol=self.symbol, frame=res)
        else:
            return res

    # NO SETTING ON TRADES :they are immutable events.

    def __iter__(self):
        yield from self.frame

    # TODO : aiter

    def __len__(self):
        return len(self.frame)

    def __str__(self):
        return str(self.frame)


if __name__ == "__main__":

    print(TradesViewBase.strategy().example())

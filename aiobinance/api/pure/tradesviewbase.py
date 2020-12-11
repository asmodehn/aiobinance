from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields
from datetime import datetime
from decimal import Decimal, getcontext
from typing import Iterable, List, Optional, Union

import hypothesis.strategies as st
import numpy as np
import pandas as pd
from bokeh.models import ColumnDataSource
from cached_property import cached_property
from hypothesis.strategies import composite
from tabulate import tabulate

from aiobinance.api.model.order import OrderSide
from aiobinance.api.model.trade import Trade

# Note : these are python dataclasses as pydantic cannot really typecheck dataframe content...
from aiobinance.api.model.tradeframe import TradeFrame


@dataclass(frozen=False)
class TradesViewBase:

    frame: Optional[TradeFrame] = field(init=True, default=TradeFrame())
    # market is the implicit symbol requested when updating
    # ie : just a default value when calling...
    market: Optional[str] = field(init=True, default=None)

    @cached_property
    def symbol(self) -> List[str]:
        if self.frame:
            return self.frame.symbol
        else:
            return []

    @cached_property
    def id(self) -> List[int]:
        if self.frame:
            return self.frame.id
        else:
            return []

    @staticmethod
    def strategy(max_size=5):
        return st.builds(TradesViewBase, frame=TradeFrame.strategy(max_size=max_size))

    @classmethod
    def from_trades(cls, *trades: Trade):
        return cls(frame=TradeFrame.from_tradeslist(*trades))

    def __post_init__(self):
        # setting id as index and ordering (required for slicing !)
        self.frame = TradeFrame(
            df=self.frame.df.set_index("id", drop=False).sort_index()
        )

    def as_datasource(self, side: OrderSide) -> ColumnDataSource:
        plotdf = self.frame.optimized()
        # TODO : live bokeh updates ??

        # select a subset of trades via boolean careful indexing with pandas
        if side == OrderSide.BUY:
            sided_plotdf = plotdf.loc[plotdf["is_buyer"] == True]  # noqa: E712
        elif side == OrderSide.SELL:
            # Note : for some reason "pd.Series ... is False" fails on pandas.
            # __eq__ is overloaded and has the expected behavior
            sided_plotdf = plotdf.loc[plotdf["is_buyer"] == False]  # noqa: E712
        else:
            raise NotImplementedError("More than 2 OrderSides ??")

        # dropping id column to avoid conflict. (it is still the index and should be accessible as such)
        return ColumnDataSource(sided_plotdf.drop(["id"], axis=1))

    def __call__(
        self, *, frame: Optional[TradeFrame] = None, **kwargs
    ) -> TradesViewBase:
        """ self updating the instance with new dataframe..."""
        # return same instance if no change
        if frame is None:
            return self

        popping = []
        if self.frame is None:
            # because we may have cached invalid values from initialization (self.info was None)
            popping.append("id")
            popping.append("symbol")
        else:  # otherwise we detect change leveraging pandas
            if self.frame.id != frame.id:
                popping.append("id")  # because id only depends on id
            if self.frame.symbol != frame.symbol:
                popping.append("symbol")

        # updating by updating data
        self.frame = frame

        # reapplying post_init as for new data (should not mess up with old data and eventually converge !)
        self.__post_init__()

        # and invalidating related caches
        for p in popping:
            self.__dict__.pop(p, None)

        # returning self to allow chaining
        return self

    def __contains__(self, item: Trade):
        # https://docs.python.org/2/reference/datamodel.html#object.__contains__
        # TODO : if this is a mapping, we should do that on keys...
        return item in self.frame

    def __eq__(self, other: TradesViewBase) -> bool:
        assert isinstance(
            other, TradesViewBase
        )  # in our design the type infers the columns.
        if self is other:
            # here we follow python on equality https://docs.python.org/3.6/reference/expressions.html#id12
            return True
        else:  # delegate equality to the unique member: frame
            return self.frame == other.frame

    def __getitem__(self, item: Union[int, slice, str]) -> Union[TradesViewBase, Trade]:
        # TODO : slice by time ???
        if isinstance(item, slice):
            # dataframe slice handled by pandas boolean indexer
            try:
                tf = TradeFrame(
                    df=self.frame.df.loc[item]
                )  # simple since dataframe is indexed on id
                return TradesViewBase(frame=tf)
            except TypeError as te:
                raise KeyError(f"{item} is too high a value for Trade.id ") from te
        elif isinstance(item, int):
            try:
                return Trade(
                    **self.frame.df.loc[item]
                )  # simple since dataframe is  indexed on id
            except OverflowError as oe:
                # E   OverflowError: Python int too large to convert to C long
                # pandas/_libs/hashtable_class_helper.pxi:1032: OverflowError
                raise KeyError(f"{item} is too high a value for Trade.id ") from oe
            except IndexError as ie:
                raise KeyError(f"No Trade.id matching {item}") from ie
        elif isinstance(item, str):
            tf = TradeFrame(df=self.frame.df.loc[self.frame.df["symbol"] == item])
            return TradesViewBase(
                frame=tf, market=item
            )  # set the default symbol for update call
        else:
            raise KeyError(f"Invalid index {item}")
        # TODO : select by symbol

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

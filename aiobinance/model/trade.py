from __future__ import annotations

from dataclasses import asdict, fields
from datetime import datetime
from decimal import Decimal, getcontext
from typing import Iterable, List, Optional, Union

import hypothesis.strategies as st
import numpy as np
import pandas as pd
from hypothesis.strategies import composite
from pydantic import validator
from pydantic.dataclasses import dataclass

# Leveraging pydantic to validate based on type hints
from tabulate import tabulate


@dataclass(frozen=True)
class Trade:
    # REMINDER : as 'precise' and 'pythonic' semantic as possible
    time: datetime
    symbol: str  # TODO : improve
    id: int
    price: Decimal
    qty: Decimal
    quote_qty: Decimal
    commission: Decimal
    commission_asset: str  # TODO : improve
    is_buyer: bool
    is_maker: bool

    order_id: Optional[
        int
    ] = None  # some source (hummingbot) might not have the accurate int... # TODO : investigate...
    order_list_id: Optional[
        int
    ] = None  # None replaces the cryptic '-1' of binance data when not part of a list TODO!!
    is_best_match: Optional[
        bool
    ] = None  # outside of binance, we might not have this information

    @validator("time", pre=True)
    def convert_pandas_timestamp(cls, v):
        if isinstance(v, pd.Timestamp):
            return v.to_pydatetime()
        return v

    def __str__(self) -> str:
        s = f"""
time: {self.time}
symbol: {self.symbol}
id: {self.id}
price: {self.price}
qty: {self.qty}
quote_qty: {self.quote_qty}
commission: {self.commission} {self.commission_asset}
is_buyer: {self.is_buyer}
is_maker: {self.is_maker}
order_id: {self.order_id}
order_list_id: {self.order_list_id}
is_best_match: {self.is_best_match}
"""
        return s

    def __dir__(self) -> Iterable[str]:
        # hiding private methods and data validators
        return [f.name for f in fields(self)]


class TradeFrame:
    _df: pd.DataFrame

    @property
    def time(self) -> List[datetime]:
        return self._df.time.to_list()

    @property
    def symbol(self) -> List[str]:  # TODO : improve
        return self._df.symbol.to_list()

    @property
    def id(self) -> List[int]:
        return self._df.id.to_list()

    @property
    def price(self) -> List[Decimal]:
        return self._df.price.to_list()

    @property
    def qty(self) -> List[Decimal]:
        return self._df.qty.to_list()

    @property
    def quote_qty(self) -> List[Decimal]:
        return self._df.quote_qty.to_list()

    @property
    def commission(self) -> List[Decimal]:
        return self._df.commission.to_list()

    @property
    def commission_asset(self) -> List[str]:  # TODO : improve
        return self._df.commission_asset.to_list()

    @property
    def is_buyer(self) -> List[bool]:
        return self._df.is_buyer.to_list()

    @property
    def is_maker(self) -> List[bool]:
        return self._df.is_maker.to_list()

    # TODO
    #  order_id: Optional[int]
    #  order_list_id: Optional[int]
    #  is_best_match: Optional[bool]

    @staticmethod
    def create(*trades: Trade) -> TradeFrame:
        """ functional create pattern, returning identical EmptyTradeFrame when appropriate..."""
        if not trades:
            return EmptyTradeFrame
        else:
            return TradeFrame(*trades)

    def __init__(self, *trades: Trade):
        # Here we follow binance format and enforce proper python types

        ids = [t.id for t in trades]
        assert len(set(ids)) == len(ids)  # ids must be unique !

        df = pd.DataFrame.from_records(
            [asdict(dc) for dc in trades], columns=[f.name for f in fields(Trade)]
        )

        self._df = df

    def __contains__(self, item: Trade):
        # BAD... TODO : make a second index out of 'id' ???
        for t in self:
            if t == item:
                return True
        return False

    def __getitem__(self, item: Union[int, slice]):  # TODO : slice
        if isinstance(item, slice):
            assert item.step is None
            start = 0 if item.start is None else item.start
            stop = len(self) if item.stop is None else item.stop

            if stop <= 0 or start >= len(self) or start >= stop:
                return EmptyTradeFrame  # returns the empty immutable tradeframe.

            if start <= 0 and stop >= len(self):
                return self  # whole slice returns the exact same instance, avoiding duplication.

            # step is always 1 here, we do not want to skip anything or aggregate trades
            subtrades = []
            for t in self._df.itertuples(index=True):
                if start <= t.Index < stop:
                    td = {f: v for f, v in t._asdict().items() if f != "Index"}
                    subtrades.append(Trade(**td))
                if stop is not None and t.Index > stop:
                    break  # early break after stop
            return TradeFrame(*subtrades)

        elif isinstance(item, int):
            if -len(self) <= item < len(self):
                return Trade(**self._df.iloc[item])
            elif item in self.id:
                return Trade(
                    **self._df[self._df.id == item].iloc[0]
                )  # iloc[0] makes 'id' look like an index even more...
            else:
                raise KeyError(f"No Trade with index {item} or id {item}")

        else:
            raise KeyError(f"Invalid index {item}")

    # NO SETTING ON TRADES :they are immutable events.

    def __iter__(self):
        for t in self._df.itertuples(index=False):
            yield Trade(**t._asdict())

    def __len__(self):
        return len(self._df)

    def __str__(self):
        # optimize before display (high decimal precision is not manageable by humans)
        optdf = self.optimized()
        return tabulate(optdf, headers="keys", tablefmt="psql")

    def optimized(
        self,
    ) -> pd.DataFrame:  # returns a raw DataFrame, containing numpy data, ready for fast compute.
        """ optimize data for simplicity and speed, dropping precision."""
        opt_copy = self._df.copy(deep=True)
        opt_copy.convert_dtypes()
        # also convert decimal to floats, losing precision
        opt_copy.price = opt_copy.price.to_numpy("float64")
        opt_copy.qty = opt_copy.qty.to_numpy("float64")
        opt_copy.quote_qty = opt_copy.quote_qty.to_numpy("float64")
        opt_copy.commission = opt_copy.commission.to_numpy("float64")
        return opt_copy


# Single empty tradeframe
EmptyTradeFrame = TradeFrame()


# Strategies, inferring attributes from type hints by default
def st_trades():
    return st.builds(
        Trade,
        id=st.integers(
            min_value=1000
        ),  # to avoid overlap of index and ids integers... TODO : validate in real usecase...
        price=st.decimals(allow_nan=False, allow_infinity=False),
        qty=st.decimals(allow_nan=False, allow_infinity=False),
        quote_qty=st.decimals(allow_nan=False, allow_infinity=False),
        commission=st.decimals(allow_nan=False, allow_infinity=False),
    )


@st.composite
def st_tradeframes(draw):
    tl = draw(st.lists(elements=st_trades(), max_size=5, unique_by=lambda t: t.id))
    return TradeFrame.create(*tl)

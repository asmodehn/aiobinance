from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields
from datetime import datetime
from decimal import Decimal, getcontext
from typing import Iterable, List, Optional, Union

import hypothesis.strategies as st
import numpy as np
import pandas as pd
from cached_property import cached_property
from hypothesis.strategies import composite
from pydantic import validator

# Leveraging pydantic to validate based on type hints
from tabulate import tabulate

from aiobinance.api.model.trade import Trade


# Note : these are python dataclasses as pydantic cannot really typecheck dataframe content...
@dataclass(frozen=True)
class TradeFrame:
    df: Optional[pd.DataFrame] = field(
        init=True,
        default=pd.DataFrame.from_records([], columns=[f.name for f in fields(Trade)]),
    )

    # @property
    # def time(self) -> List[datetime]:
    #     return self.df.time.to_list()
    #
    # @property
    # def symbol(self) -> List[str]:  # TODO : improve
    #     return self.df.symbol.to_list()

    @cached_property
    def id(self) -> List[int]:
        return self.df.id.to_list()

    # TODO : put this in a  meta class to have it tied to the type itself !
    @classmethod
    def id_min(cls):
        return np.iinfo(np.dtype("uint64")).min

    @classmethod
    def id_max(cls):
        return np.iinfo(np.dtype("uint64")).max

    #
    # @property
    # def price(self) -> List[Decimal]:
    #     return self.df.price.to_list()
    #
    # @property
    # def qty(self) -> List[Decimal]:
    #     return self.df.qty.to_list()
    #
    # @property
    # def quote_qty(self) -> List[Decimal]:
    #     return self.df.quote_qty.to_list()
    #
    # @property
    # def commission(self) -> List[Decimal]:
    #     return self.df.commission.to_list()
    #
    # @property
    # def commission_asset(self) -> List[str]:  # TODO : improve
    #     return self.df.commission_asset.to_list()
    #
    # @property
    # def is_buyer(self) -> List[bool]:
    #     return self.df.is_buyer.to_list()
    #
    # @property
    # def is_maker(self) -> List[bool]:
    #     return self.df.is_maker.to_list()

    # TODO
    #  order_id: Optional[int]
    #  order_list_id: Optional[int]
    #  is_best_match: Optional[bool]

    @st.composite
    @staticmethod
    def strategy(draw, max_size=5):
        tl = st.lists(
            elements=Trade.strategy(), max_size=max_size, unique_by=lambda t: t.id
        )
        return TradeFrame.from_tradeslist(*draw(tl))

    @classmethod
    def from_tradeslist(cls, *trades: Trade):
        # related : https://github.com/pandas-dev/pandas/issues/9216
        # building structured numpy array to specify optimal dtypes
        # Ref : https://numpy.org/doc/stable/user/basics.rec.html

        arraylike = [tuple(asdict(dc).values()) for dc in trades]

        npa = np.array(arraylike, dtype=Trade.as_dtype())  # Drops timezone info...
        # df = pd.DataFrame(data={
        #     c: npa[c] for c, t in Trade.as_dtype()
        # })

        df = pd.DataFrame(
            data=npa
        )  # TODO : use nparray directly ??? CAREFUL : numpy doesnt do timezones...

        return cls(df=df)

    def __contains__(self, item: Trade):
        for t in self:  # iterates and cast to Trade
            if t == item:  # using Trade equality
                return True
        return False

    def __eq__(self, other: TradeFrame) -> bool:
        assert isinstance(
            other, TradeFrame
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
            tf = TradeFrame(df=self.df[item])
            return tf

        elif isinstance(item, int):
            try:
                return Trade(**self.df.iloc[item])
            except IndexError as ie:
                raise KeyError("TradeFrame index out of range") from ie
        else:
            raise KeyError(f"Invalid index {item}")

    # NO SETTING ON TRADES :they are immutable events.

    def __iter__(self):
        for t in self.df.itertuples(index=False):
            yield Trade(**t._asdict())

    def __len__(self):
        return len(self.df)

    def __add__(self, other: TradeFrame):
        # At the frame level we ignore the index (unintended record ordering)
        return TradeFrame(
            df=self.df.append(other.df, ignore_index=True, verify_integrity=True)
        )

    def __str__(self):
        # optimize before display (high decimal precision is not manageable by humans)
        optdf = self.optimized()
        return tabulate(optdf, headers="keys", tablefmt="psql")

    def optimized(
        self,
    ) -> pd.DataFrame:  # returns a raw DataFrame, containing numpy data, ready for fast compute.
        """ optimize data for simplicity and speed, dropping precision."""
        opt_copy = self.df.copy(deep=True)
        opt_copy.convert_dtypes()
        # also convert decimal to floats, losing precision
        opt_copy.price = opt_copy.price.to_numpy("float64")
        opt_copy.qty = opt_copy.qty.to_numpy("float64")
        opt_copy.quote_qty = opt_copy.quote_qty.to_numpy("float64")
        opt_copy.commission = opt_copy.commission.to_numpy("float64")
        return opt_copy


if __name__ == "__main__":

    print(TradeFrame.strategy().example())

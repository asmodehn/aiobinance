from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields
from datetime import datetime, timezone
from decimal import Decimal, getcontext
from typing import Iterable, List, Optional, Union

import hypothesis.strategies as st
import numpy as np
import pandas as pd
from bokeh.models import ColumnDataSource
from cached_property import cached_property
from hypothesis.strategies import composite
from pydantic import validator

# Leveraging pydantic to validate based on type hints
from tabulate import tabulate

from aiobinance.api.model.order import OrderSide
from aiobinance.api.model.trade import Trade


# Note : these are python dataclasses as pydantic cannot really typecheck dataframe content...
@dataclass(frozen=True)
class TradeFrame:
    df: Optional[pd.DataFrame] = field(
        init=True,
        default=pd.DataFrame.from_records([], columns=[f.name for f in fields(Trade)]),
    )

    @property
    def empty(self) -> bool:
        return self.df.empty

    # @property
    # def time(self) -> List[datetime]:
    #     return self.df.time.to_list()

    @property
    def symbol(self) -> List[str]:  # TODO : improve
        return self.df.symbol.to_list()

    @property
    def id(self) -> List[int]:
        return self.df.index.to_list()

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
            elements=Trade.strategy(),
            max_size=max_size,
            unique_by=lambda t: t.id,  # unique by id only
        )
        tls = draw(tl)
        return TradeFrame.from_tradeslist(*tls)

    @classmethod
    def from_tradeslist(cls, *trades: Trade):
        # related : https://github.com/pandas-dev/pandas/issues/9216
        # building structured numpy array to specify optimal dtypes
        # Ref : https://numpy.org/doc/stable/user/basics.rec.html

        arraylike = [
            tuple(
                # explicitely drop timezone after converting to UTC
                v.astimezone(tz=timezone.utc).replace(tzinfo=None)
                if isinstance(v, datetime)
                else v
                for v in asdict(t).values()
            )
            for t in trades
        ]

        npa = np.array(
            arraylike, dtype=list(Trade.as_dtype().items())
        )  # Drops timezone info (because numpy)

        df = pd.DataFrame(
            data=npa
        )  # TODO : use nparray directly ??? CAREFUL : numpy doesnt do timezones...

        return cls(df=df)

    def as_datasource(self) -> ColumnDataSource:
        plotdf = self.optimized()
        # TODO : live bokeh updates ??

        # build plot datasource depending on whos asking for it
        plotdf["price_boughtsold"] = np.where(plotdf["is_buyer"], "BOUGHT", "SOLD")

        # dropping id column to avoid conflict. (it is still the index and should be accessible as such)
        return ColumnDataSource(plotdf.drop(["id"], axis=1))

    def __post_init__(self):
        # Here we follow binance format and enforce proper types and structure

        if self.df.empty:
            # Note: an empty df is a special case, as open_time is still a column...
            return

        # shaping dataframe if needed
        # detecting index origin via its name (default index name is None)
        if self.df.index.name != "id":
            assert "id" in self.df.columns
            # Mutating df under the hood... CAREFUL : we heavily rely on (buggy?) pandas here...
            self.df.reset_index(drop=True, inplace=True)
            # enforcing id unicity
            self.df.drop_duplicates(subset=["id"], keep="last", inplace=True)
            # use the time_utc column as an index
            self.df.set_index(
                self.df["id"],
                verify_integrity=True,
                inplace=True,
            )
            # remove it as a column to remove ambiguity
            self.df.drop("id", axis="columns", inplace=True)
            # sort via the index
            self.df.sort_index(inplace=True)

            # explicit assumption for every other operation on the dataframe :
            assert "id" not in self.df.columns
            assert self.df.index.name == "id"

            # finally enforcing dtypes:
            # TODO

    def __contains__(self, item: Union[Trade, int, datetime]):
        if isinstance(item, Trade):
            for t in self:  # iterates and cast to Trade
                if t == item:  # using Trade equality
                    return True
        elif isinstance(item, int):
            for t in self:
                if t.id == item:
                    return True
        elif isinstance(
            item, datetime
        ):  # exact match (TODO : maybe take first trade before and first after ?)
            if (
                item.tzinfo is None
            ):  # because we will do a tz-aware comparison with item
                item = item.replace(tzinfo=timezone.utc)
            # converting datetime to utc in any case
            item = item.astimezone(tz=timezone.utc)

            for t in self:
                # Note : same semantics as getitem
                if (
                    t.time_utc == item  # CAREFUL: tz-aware comparison
                ):  # checking *exact* time match
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

    def __getitem__(  # noqa: C901
        self, item: Union[int, datetime, slice, str]
    ) -> Union[TradeFrame, Trade]:
        if isinstance(item, int):
            try:
                rs = self.df.loc[item]  # because id is our index

                return Trade(
                    **{
                        self.df.index.name: item,  # recovering trade id (index value)
                        **rs.to_dict(),
                    }
                )

            except OverflowError as oe:
                # E   OverflowError: Python int too large to convert to C long
                # pandas/_libs/hashtable_class_helper.pxi:1032: OverflowError
                raise KeyError(f"{item} is too high a value for Trade.id ") from oe
            except IndexError as ie:
                raise KeyError(f"No Trade.id matching {item}") from ie
        elif isinstance(item, datetime):
            if item.tzinfo is not None:
                # converting datetime to unaware timezone, in utc. to allow comparison with unaware numpy values.
                item = item.astimezone(tz=timezone.utc).replace(tzinfo=None)

            rs = self.df.loc[self.df.time_utc.astype(dtype="datetime64[us]") == item]

            if len(rs) == 1:
                return Trade(**rs.reset_index(drop=False).iloc[0])
            elif len(rs) == 0:
                raise KeyError(f"Invalid index {item}")
            else:
                return TradeFrame(df=rs)

        elif isinstance(item, slice):
            if item.start is None and item.stop is None:
                return TradeFrame(df=self.df.copy())  # just duplicate data

            # relying on pandas indexing if slice of ids:
            if isinstance(item.start, int) or isinstance(item.stop, int):
                return TradeFrame(df=self.df.loc[item])

            # Otherwise: dataframe slice handled by pandas boolean indexer
            try:
                selector = pd.Series({i: True for i in self.df.index})

                if item.start is not None:
                    if isinstance(item.start, datetime):
                        if item.start.tzinfo is not None:
                            # converting datetime to unaware timezone, in utc. to allow comparison with unaware numpy values.
                            start = item.start.astimezone(tz=timezone.utc).replace(
                                tzinfo=None
                            )
                        else:
                            start = item.start
                        selector = selector & (
                            start <= self.df.time_utc.astype(dtype="datetime64[us]")
                        )
                if item.stop is not None:
                    if isinstance(item.stop, datetime):
                        if item.stop.tzinfo is not None:
                            stop = item.stop.astimezone(tz=timezone.utc).replace(
                                tzinfo=None
                            )
                        else:
                            stop = item.stop
                        selector = selector & (
                            self.df.time_utc.astype(dtype="datetime64[us]") <= stop
                        )

                df = self.df.loc[selector]

            except TypeError as te:
                raise KeyError(
                    f"{item} is too high a value for Trade.time_utc or Trade.id "
                ) from te

            return TradeFrame(df=df)

        if isinstance(item, str):
            df = self.df.loc[self.df["symbol"] == item]
            return TradeFrame(df=df)  # set the default symbol for update call
        else:
            raise KeyError(f"Invalid index {item}")

    # NO SETTING ON TRADES :they are immutable events.

    def __iter__(self):
        for t in self.df.itertuples(index=True):
            # CAREFUL : reset_index may create an index column (BUG ?)
            yield Trade(
                **{
                    self.df.index.name if k == "Index" else k: v
                    for k, v in t._asdict().items()
                }
            )

    def __len__(self):
        return len(self.df)

    # Ref : https://docs.python.org/3.8/library/stdtypes.html#set.intersection
    def intersection(self, other: TradeFrame):
        # extracting candles when there is *exact* equality
        trades = []
        # very naive implementation. TODO : optimize
        for t in self:
            if t in other:
                trades.append(t)

        return TradeFrame.from_tradeslist(*trades)

    # Ref : https://docs.python.org/3.8/library/stdtypes.html#set.union
    def union(self, other: TradeFrame):

        # special empty case => return the other one.
        # This avoid different columns issue when dataframe is empty (open_time is not the index - pandas 1.1.5)
        if self.df.empty:
            return TradeFrame(df=other.df.copy(deep=True))
        if other.df.empty:
            return TradeFrame(df=self.df.copy(deep=True))

        # otherwise we need to merge
        newdf_noidx = self.df.reset_index(drop=False).merge(
            other.df.reset_index(drop=False), how="outer"
        )

        # Note : previous merging attempts with "aggregate" and fonction application failed
        # on tricky bugs/pandas limitations...
        # Attempting a different way based on resolving duplicates in groups and replacing.
        dups = newdf_noidx.duplicated(subset="id", keep=False)

        dupgroups = newdf_noidx[dups].groupby(by="id")

        # keeping all non-duplicates in boolean filter
        grpfltr = ~newdf_noidx.id.isin(dupgroups.groups)

        for grp, frm in dupgroups:
            best_idx = frm.iloc[0].name  # picking first in frame
            # We could here implement some kind of clever merging if it becomes necessary (like for OHLCFrame)...

            # merge in group filter (set it to true, all other in same group must remain false)
            grpfltr = grpfltr | (grpfltr.index == best_idx)

        # replace groups into merged dataframe
        newdf_noidx = newdf_noidx[grpfltr]

        # the OHLCFrame constructor will reindex properly.
        return TradeFrame(df=newdf_noidx)

    # Ref : https://docs.python.org/3.8/library/stdtypes.html#set.difference
    def difference(self, other: TradeFrame):
        # finding identical indexes in both dataframe, and extracting subset

        ix = self.intersection(other)

        trades = []
        # very naive implementation. TODO : optimize
        # Reminder : this is just a set of candles, no candle merging.
        for t in self:
            # Note : in case of conflict (same index, different values), this has the effect of
            #        ignoring other and prioritizing having candles from self in result.
            if t not in ix:
                trades.append(t)

        return TradeFrame.from_tradeslist(*trades)

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

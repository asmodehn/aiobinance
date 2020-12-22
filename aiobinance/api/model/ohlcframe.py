from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields
from datetime import MAXYEAR, MINYEAR, datetime, timedelta
from decimal import Decimal
from typing import Iterable, List, Optional, Union

import hypothesis.strategies as st
import numpy as np
import pandas as pd
from bokeh.models import BooleanFilter, CDSView, ColumnDataSource, Legend
from bokeh.plotting import Figure
from hypothesis import assume, infer
from hypothesis.strategies import SearchStrategy
from pandas import merge_ordered
from pandas._libs.tslibs.np_datetime import OutOfBoundsDatetime
from pydantic import validator

# Leveraging pydantic to validate based on type hints
from tabulate import tabulate

from aiobinance.api.model.pricecandle import PriceCandle


# Note : these are python dataclasses as pydantic cannot really typecheck dataframe content...
@dataclass(frozen=True)
class OHLCFrame:  # TODO : manipulating th class itself (with a meta class) can help us enforce correct shape of dataframe...

    df: Optional[pd.DataFrame] = field(
        init=True,
        default=pd.DataFrame.from_records(
            [], columns=[f.name for f in fields(PriceCandle)]
        ),
    )

    @property
    def empty(self) -> bool:
        return self.df.empty

    # properties to make it quack like a candle...
    @property
    def open_time(self) -> datetime:  # TODO: special case for empty df
        return self.df.index[0].to_pydatetime()

    @property
    def close_time(self) -> datetime:  # TODO: special case for empty df
        return self.df.close_time[-1].to_pydatetime()

    @property
    def open(self) -> Decimal:
        return self.df.open[0]

    @property
    def high(self) -> Decimal:
        return max(self.df.high)

    @property
    def low(self) -> Decimal:
        return min(self.df.low)

    @property
    def close(self) -> Decimal:
        return self.df.close[-1]

    @st.composite
    @staticmethod
    def strategy(
        draw,
        tfs: SearchStrategy = st.timedeltas(
            min_value=timedelta(
                microseconds=1  # we do not want any timeframe <= 0
                # timeframe has a non-null duration semantic ==>> always > 0
            ),  # no point being crazy about time frame (need to fit in [MINYEAR..MAXYEAR])
            max_value=timedelta(days=100),  # big enough max delta
        ),
        max_size=5,
    ):

        # we want consistent time frame for all candles
        # so from tfs we derive a list of candles, and then pick opentimes, and from it compute close times
        candles = draw(
            tfs.flatmap(
                lambda tf: st.lists(
                    elements=PriceCandle.strategy(
                        time_deltas=st.just(tf),
                        timebounds=st.datetimes(  # no need to be extra precise on max bound here, given pandas limitations
                            min_value=pd.to_datetime(pd.Timestamp.min),
                            max_value=pd.to_datetime(pd.Timestamp.max) - tf,
                        ).flatmap(
                            lambda ot: st.tuples(st.just(ot), st.just(ot + tf))
                        ),
                    ),
                    max_size=max_size,
                    unique_by=lambda c: c.open_time,
                )
            )  # preventing equal opentime (to use as index), but allowing time overlap
        )
        # REMINDER : we do not intend here to prevent candle overlap.
        # Currently, it must be supported in operations on OHLCFrame.

        return OHLCFrame.from_candleslist(*candles)

    @classmethod
    def from_candleslist(cls, *candles: PriceCandle):
        arraylike = [tuple(asdict(dc).values()) for dc in candles]
        npa = np.array(
            arraylike, dtype=list(PriceCandle.as_dtype().items())
        )  # Drops timezone info...

        df = pd.DataFrame(data=npa)
        return cls(df=df)

    def as_datasource(self, compute_mid_time=True) -> ColumnDataSource:
        plotdf = self.optimized()
        if compute_mid_time:
            timeinterval = plotdf.open_time[1] - plotdf.open_time[0]
            plotdf["mid_time"] = plotdf.open_time + timeinterval / 2

        return ColumnDataSource(plotdf)

    def __post_init__(self):
        # Here we follow binance format and enforce proper types and structure

        if not self.df.empty and (
            self.df.index.name != "open_time"
            or not isinstance(self.df.index, pd.DatetimeIndex)
        ):
            assert "open_time" in self.df.columns
            # Mutating df under the hood... CAREFUL : we heavily rely on (buggy?) pandas here...
            self.df.reset_index(drop=True, inplace=True)
            # use the open_time column as an index
            self.df.set_index(
                pd.to_datetime(self.df["open_time"]),
                verify_integrity=True,
                inplace=True,
            )
            # remove it as a column to remove ambiguity
            self.df.drop("open_time", axis="columns", inplace=True)
            # sort via the index
            self.df.sort_index(inplace=True)

            # explicit assumption for every other operation on the dataframe :
            assert "open_time" not in self.df.columns
            assert isinstance(self.df.index, pd.DatetimeIndex)
            assert self.df.index.name == "open_time"

            # finally enforcing dtypes:

        # Note: an empty df is a special case, as open_time is still a column...

    def __contains__(self, item: Union[PriceCandle, datetime]) -> bool:
        # https://docs.python.org/2/reference/datamodel.html#object.__contains__
        if isinstance(item, PriceCandle):
            for t in self:  # iterates and cast to PriceCandle
                if t == item:  # using Trade equality
                    return True
            return False
        elif isinstance(item, datetime):  # continuous index
            for t in self:
                # Note : same semantics as getitem
                if (
                    t.open_time <= item <= t.close_time
                ):  # checking one candle contains the datetime
                    return True
            return False
        else:
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

    def __getitem__(
        self, item: Union[datetime, slice]
    ) -> Union[OHLCFrame, PriceCandle]:
        if isinstance(item, slice):
            # dataframe slice handled by pandas boolean indexer
            try:
                return OHLCFrame(
                    df=self.df.loc[item]
                )  # simple since dataframe is indexed on datetime
            except TypeError as te:
                raise KeyError(
                    f"{item} is too high a value for PriceCandle.open_time "
                ) from te
        elif isinstance(item, datetime):
            try:
                rs = self.df.loc[  # self.df.index.to_series().astype(dtype='datetime64[us]') ]  # using index as such
                    # OLD : finding containing candle...
                    (  # REMINDER : precision matters here (python datetime precision is microsecond)
                        self.df.index.to_series().astype(dtype="datetime64[us]") <= item
                    )  # CAREFUL with time bounds semantics !
                    # Note we want to err towards using open_time as index, not close time, in case one == the other...
                    & (item <= self.df.close_time.astype(dtype="datetime64[us]"))
                ]

                if len(rs) == 1:
                    return PriceCandle(
                        **rs.reset_index(drop=False).iloc[0]
                    )  # simple since dataframe is  indexed on id
                elif len(rs) == 0:
                    raise KeyError(f"Invalid index {item}")
                else:
                    # Multiple matches return another frame
                    return OHLCFrame(df=rs)

            except OutOfBoundsDatetime as oobd:
                # TODO : handle/prevent overflow error when int is too large to be optimized by pandas/numpy
                # E   OverflowError: Python int too large to convert to C long
                # pandas/_libs/hashtable_class_helper.pxi:1032: OverflowError
                raise KeyError(f"{item} out of bounds ") from oobd
            except IndexError as ie:
                raise KeyError(f"No PriceCandle.open_time matching {item}") from ie
        else:
            raise KeyError(f"Invalid index {item}")

    def __iter__(self):
        for t in self.df.itertuples(index=True):
            # CAREFUL : reset_index may create an index column (BUG ?)
            # yield PriceCandle(**{k: v for k, v in t._asdict().items() if k != 'index'})
            yield PriceCandle(
                **{
                    self.df.index.name if k == "Index" else k: v
                    for k, v in t._asdict().items()
                }
            )

    def __len__(self):
        return len(self.df)

    # Ref : https://docs.python.org/3.8/library/stdtypes.html#set.intersection
    def intersection(self, other: OHLCFrame):
        # extracting candles when there is *exact* equality
        candles = []
        # very naive implementation. TODO : optimize
        # REMINDER : this is just a set of candle, no candle merging.
        # TODO : somehow enforce same timeframe...
        for t in self:
            if t in other:
                candles.append(t)

        return OHLCFrame.from_candleslist(*candles)

    # Ref : https://docs.python.org/3.8/library/stdtypes.html#set.union
    def union(self, other: OHLCFrame):

        # special empty case => return the other one.
        # This avoid different columns issue when dataframe is empty (open_time is not the index - pandas 1.1.5)
        if self.df.empty:
            return OHLCFrame(df=other.df.copy(deep=True))
        if other.df.empty:
            return OHLCFrame(df=self.df.copy(deep=True))

        # otherwise it is safe to merge
        newdf_noidx = merge_ordered(
            # dropping indexes to retrieve the open_time column when aggregating.
            self.df.reset_index(drop=False),
            other.df.reset_index(drop=False),
            fill_method=None,
        )
        # newdf = merge_ordered(self.df, other.df, fill_method=None, on=self.df.index)
        # newdf_noidx = self.df.merge(other.df, how='outer', left_index=True, sort=True)

        # seems aggregate needs a state to compare multiple rows
        chosen = pd.Series()

        # This is necessary to handle conflicting data (same index, different values... which to pick ?)
        def stitcher(row: pd.Series, **kwargs) -> pd.Series:
            nonlocal chosen

            # early return if we get passed an empty row (no field in series)
            if len(row) == 0:
                return row

            # otherwise we use external state, to be able to chose between multiple rows
            if chosen.get("open_time", None) != row["open_time"] or (
                # no chosen, or different index => take new row
                # same index : we need to compare rows on num_trades, volume, high and low
                chosen["num_trades"] < row["num_trades"]
                or chosen["volume"] < row["volume"]
                # careful with strictness when comparing high and low bounds...
                or (chosen["high"] < row["high"] and chosen["low"] >= row["low"])
                or (chosen["high"] <= row["high"] and chosen["low"] > row["low"])
            ):  # in that case pick the new row
                chosen = row.copy()
                assert (chosen == row).all()  # TMP : attempting to find a bug...
            # otherwise just keep the old one, discarding new information
            # because we are not sure we should integrate it or not.
            # It seems there is less information in the new candle than in the original one, better stay safe.

            # Note : we dont want a more complex algorithm,
            # because we don't want to aggregate and merge candles themselves.
            # We just need to pick the one with more information,
            # hoping to eventually converge when there is multiple sources (different API server responding)

            return chosen

        # only check open_time to identify duplicates, other columns might be different
        newdf = newdf_noidx.agg(stitcher, axis=1).drop_duplicates(
            subset="open_time", keep="last"
        )
        # Tried group by or named aggregate, but they don't seems to work as we would need...

        # the OHLCFrame constructor will reindex properly.
        return OHLCFrame(df=newdf)

        # Ref : https://docs.python.org/3.8/library/stdtypes.html#set.difference

    def difference(self, other: OHLCFrame):
        # finding identical indexes in both dataframe, and extracting subset

        ix = self.intersection(other)

        candles = []
        # very naive implementation. TODO : optimize
        # Reminder : this is just a set of candles, no candle merging.
        for t in self:
            # Note : in case of conflict (same index, different values), this has the effect of
            #        ignoring other and prioritizing having candles from self in result.
            if t not in ix:
                candles.append(t)

        return OHLCFrame.from_candleslist(*candles)

    def __str__(self):
        # optimize before display (high decimal precision is not manageable by humans)
        optdf = self.optimized()
        return tabulate(optdf, headers="keys", tablefmt="psql")

    def optimized(self) -> pd.DataFrame:
        opt_copy = self.df.copy(deep=True)
        opt_copy.convert_dtypes()
        return opt_copy


if __name__ == "__main__":
    print(OHLCFrame.strategy().filter(lambda f: len(f) > 0).example())

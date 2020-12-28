from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields
from datetime import MAXYEAR, MINYEAR, datetime, timedelta, timezone
from decimal import Decimal
from typing import Iterable, List, Optional, Union

import hypothesis.strategies as st
import numpy as np
import pandas as pd
from bokeh.models import BooleanFilter, CDSView, ColumnDataSource, Legend
from bokeh.plotting import Figure
from hypothesis import assume, infer
from hypothesis.strategies import SearchStrategy
from pandas import merge, merge_ordered
from pandas._libs.tslibs.np_datetime import OutOfBoundsDatetime
from pydantic import validator

# Leveraging pydantic to validate based on type hints
from tabulate import tabulate

from aiobinance.api.model.pricecandle import PriceCandle


# Note : these are python dataclasses as pydantic cannot really typecheck dataframe content...
@dataclass(frozen=True)
class OHLCFrame:  # TODO : manipulating th class itself (with a meta class) can help us enforce correct shape of dataframe...

    # TODO : we should probably make the timeinterval (timeframe) part of the type here...
    interval: Optional[timedelta] = field(
        init=False,  # we determine that from the dataframe in __post_init__
        default=None,
    )

    df: Optional[pd.DataFrame] = field(
        init=True,
        default=pd.DataFrame(
            data=np.array([], dtype=list(PriceCandle.as_dtype().items()))
        ),
    )

    @property
    def empty(self) -> bool:
        return self.df.empty

    # properties to make it quack like a candle...
    @property
    def open_time(self) -> Optional[datetime]:
        if self.df.empty:
            return None
        else:
            return self.df.index[0].to_pydatetime().replace(tzinfo=timezone.utc)

    @property
    def close_time(self) -> Optional[datetime]:
        if self.df.empty:
            return None
        else:
            return self.df.close_time[-1].to_pydatetime().replace(tzinfo=timezone.utc)

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
        arraylike = [
            tuple(
                # explicitely drop timezone after converting to UTC
                v.astimezone(tz=timezone.utc).replace(tzinfo=None)
                if isinstance(v, datetime)
                else v
                for v in asdict(dc).values()
            )
            for dc in candles
        ]

        npa = np.array(
            arraylike, dtype=list(PriceCandle.as_dtype().items())
        )  # Drops timezone info (because numpy)

        df = pd.DataFrame(data=npa)
        return cls(df=df)

    def as_datasource(
        self, compute_mid_time=True, compute_upwards=True
    ) -> ColumnDataSource:
        plotdf = self.optimized()
        if not plotdf.empty:
            # we need to replicate index column (to match empty df behavior - pandas oddities)
            plotdf["index"] = plotdf.index  # TODO : index should remain simply numeric
            # TODO: It could then be used to track positions in differences and patches (cf. plot updates)
        if compute_mid_time:
            if not plotdf.empty:
                plotdf["mid_time"] = plotdf.index + self.interval / 2
            else:  # if no index to use for computation, duplicate close_time column
                plotdf["mid_time"] = plotdf["close_time"].copy()
        if compute_upwards:
            plotdf["upwards"] = np.where(plotdf.open < plotdf.close, "UP", "DOWN")
        cds = ColumnDataSource(plotdf)
        return cds

    def __post_init__(self):
        # Here we follow binance format and enforce proper types and structure

        if self.df.empty:
            # Note: an empty df is a special case, as open_time is still a column...
            return

        # shaping dataframe if needed
        if self.df.index.name != "open_time" or not isinstance(
            self.df.index, pd.DatetimeIndex
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

        # setting interval timedelta automatically
        object.__setattr__(
            self,
            "interval",  # We need to restrict ourselves to ONE candle here
            (self.df.iloc[0].close_time - self.df.iloc[0].name).to_pytimedelta(),
        )

    def __contains__(self, item: Union[PriceCandle, datetime]) -> bool:
        # https://docs.python.org/2/reference/datamodel.html#object.__contains__
        if isinstance(item, PriceCandle):
            for t in self:  # iterates and cast to PriceCandle
                if t == item:  # using Trade equality
                    return True
        elif isinstance(item, datetime):  # continuous index
            if (
                item.tzinfo is None
            ):  # because we will do a tz-aware comparison with item
                item = item.replace(tzinfo=timezone.utc)
            # converting datetime to utc in any case
            item = item.astimezone(tz=timezone.utc)

            for t in self:
                # Note : same semantics as getitem
                if (
                    t.open_time <= item <= t.close_time  # CAREFUL: tz-aware comparison
                ):  # checking one candle contains the datetime
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

    def __getitem__(
        self, item: Union[datetime, slice]
    ) -> Union[OHLCFrame, PriceCandle]:
        if isinstance(item, slice):
            """On a slice we also pick the border candles """
            start = item.start
            stop = item.stop
            if start is not None and start.tzinfo is not None:
                # converting datetime to unaware timezone, in utc. to allow comparison with unaware numpy values.
                start = start.astimezone(tz=timezone.utc).replace(tzinfo=None)

            if stop is not None and stop.tzinfo is not None:
                stop = stop.astimezone(tz=timezone.utc).replace(tzinfo=None)

            # sanitizing slice...
            item = slice(start, stop)

            # dataframe slice handled by pandas boolean indexer
            try:
                selector = pd.Series({i: True for i in self.df.index})

                if item.start is not None and item.start >= self.open_time.replace(
                    tzinfo=None
                ):
                    selector = selector & (
                        item.start <= self.df.close_time.astype(dtype="datetime64[us]")
                    )

                if item.stop is not None and item.stop <= self.close_time.replace(
                    tzinfo=None
                ):
                    selector = selector & (
                        self.df.index.to_series().astype(dtype="datetime64[us]")
                        <= item.stop
                    )

                df = self.df.loc[selector]

            except TypeError as te:
                raise KeyError(
                    f"{item} is too high a value for PriceCandle.open_time "
                ) from te

            return OHLCFrame(df=df)
        elif isinstance(item, datetime):

            if item.tzinfo is not None:
                # converting datetime to unaware timezone, in utc. to allow comparison with unaware numpy values.
                item = item.astimezone(tz=timezone.utc).replace(tzinfo=None)

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

        # otherwise we need to merge
        newdf_noidx = self.df.reset_index(drop=False).merge(
            other.df.reset_index(drop=False), how="outer"
        )

        # Note : previous merging attempts with "aggregate" and fonction application failed
        # on tricky bugs/pandas limitations...
        # Attempting a different way based on resolving dupicates in groups and replacing.
        dups = newdf_noidx.duplicated(subset="open_time", keep=False)

        dupgroups = newdf_noidx[dups].groupby(by="open_time")

        # keeping all non-duplicates in boolean filter
        grpfltr = ~newdf_noidx.open_time.isin(dupgroups.groups)

        for grp, frm in dupgroups:
            best_idx = frm.iloc[0].name  # picking first in frame
            for el in frm.itertuples():
                if (
                    el.num_trades > frm.loc[best_idx].num_trades
                    or el.volume > frm.loc[best_idx].volume
                    or (
                        (
                            el.high >= frm.loc[best_idx].high
                            and el.low < frm.loc[best_idx].low
                        )
                        or (
                            el.high > frm.loc[best_idx].high
                            and el.low <= frm.loc[best_idx].low
                        )
                    )
                ):
                    # keep only the best index
                    best_idx = (
                        el.Index
                    )  # because ".name" becomes "Index" in Pandas tuples...

            # here we have hte best candle index
            # merge in group filter (set it to true, all other in same group must remain false)
            grpfltr = grpfltr | (grpfltr.index == best_idx)

        # replace groups into merged dataframe
        newdf_noidx = newdf_noidx[grpfltr]

        # the OHLCFrame constructor will reindex properly.
        return OHLCFrame(df=newdf_noidx)

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

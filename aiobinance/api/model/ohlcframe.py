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
from cached_property import cached_property
from hypothesis import assume, infer
from hypothesis.strategies import SearchStrategy
from pandas import merge_ordered
from pandas._libs.tslibs.np_datetime import OutOfBoundsDatetime
from pydantic import validator

# Leveraging pydantic to validate based on type hints
from tabulate import tabulate

from aiobinance.api.model.pricecandle import (
    MinutePriceCandle,
    PriceCandle,
    TimeInterval,
)


# Note : these are python dataclasses as pydantic cannot really typecheck dataframe content...
@dataclass(frozen=True)
class _OHLCFrame:

    df: Optional[pd.DataFrame] = field(
        init=True,
        default=pd.DataFrame.from_records(
            [],
            columns=[
                "open_time",
                "open",
                "high",
                "low",
                "close",
                "volume",
                "close_time",
                "qav",
                "num_trades",
                "taker_base_vol",
                "taker_quote_vol",
                "is_best_match",
            ],
        ),
    )

    # Note: OHLC theoretically can have variable timestep.
    # But in practice, it is simpler (and consistent with our usecase) to have a constant timeframe.

    def __init_subclass__(
        cls, interval: TimeInterval = TimeInterval.minutely, **kwargs
    ):
        super().__init_subclass__(**kwargs)
        print(f"Called __init_subclass__({cls}, {interval})")
        cls.interval = interval

    # properties like those of a PriceCandle
    # for list of column value in the frame, access directly the frame attribute
    @cached_property
    def open_time(self) -> Optional[datetime]:
        # open_time is the index
        # TODO : drop the nanoseconds we dont need with python datetime
        return self.df.index[0] if len(self.df) > 0 else None

    @cached_property
    def close_time(self) -> Optional[datetime]:
        # TODO : drop the nanoseconds we dont need with python datetime
        return self.df.close_time[-1] if len(self.df) > 0 else None

    @st.composite
    @staticmethod
    def strategy(
        draw,
        tfs: SearchStrategy = st.timedeltas(
            min_value=timedelta(
                microseconds=1  # we do not want any timeframe <= 0
                # timeframe has a non-null duration semantic ==>> always > 0
            ),  # no point being crazy about time frame (need to fit in [MINYEAR..MAXYEAR])
            max_value=timedelta(days=100),
        ),
        max_size=5,
    ):

        # we want consistent time frame for all candles
        tf = draw(tfs)

        assert tf > timedelta()  # break early if we dont have a positive timeframe

        # generate all open times first (careful with datetime bounds)
        # TODO : review this...
        try:
            # CAREFUL: datetime min and max are different for computation
            # see supported Operations https://docs.python.org/3/library/datetime.html#datetime-objects
            otl = draw(
                st.lists(
                    elements=st.datetimes(  # no need to be extra precise on max bound here
                        min_value=datetime(year=MINYEAR, month=1, day=1),
                        max_value=datetime(year=MAXYEAR, month=12, day=31) - tf,
                    ),
                    max_size=max_size,
                )
            )
        except OverflowError as oe:
            print(f"{datetime.max} - {tf} OVERFLOWS !!!")
            raise oe

        cl = []
        for ot in otl:
            # drop times that are inside an accepted interval => prevents overlapping but allows holes in candles list
            # REMINDER : this computation is valid only at constant timeframe.
            for c in cl:
                assume(
                    not (  # CAREFUL with time bounds (verify Binance semantics on time bounds for candles)
                        c.open_time <= ot and ot <= c.close_time
                    )  # if opentime in existing interval
                    and not (c.open_time <= ot + tf and ot + tf <= c.close_time)
                )  # if closetime in existing interval
            # if we are correct in our assumption, we add it to the list
            cl.append(draw(PriceCandle.strategy(tba=st.just(ot), tbb=st.just(ot + tf))))

        return _OHLCFrame.from_candleslist(*cl)

    @classmethod
    def from_candleslist(cls, *candles: PriceCandle):
        # careful here to merge price_ with times in candle
        arraylike = []
        # TODO : proper data structure in price candle can make this trivial...
        for dc in candles:
            c = tuple
            for v in asdict(dc).values():
                if isinstance(v, dict):
                    # flattening
                    c = c + tuple(vv for vv in v.values())
                else:
                    c = c + v
            arraylike.append(c)

        npa = np.array(
            arraylike, dtype=list(PriceCandle.as_dtype().items())
        )  # Drops timezone info...
        # df = pd.DataFrame.from_records(
        #     [asdict(dc) for dc in candles],
        #     columns=[f.name for f in fields(PriceCandle)],
        # )

        df = pd.DataFrame(data=npa)
        return cls(df=df)

    def as_datasource(self, compute_mid_time=True) -> ColumnDataSource:
        plotdf = self.optimized()
        if compute_mid_time:
            timeinterval = plotdf.open_time[1] - plotdf.open_time[0]
            plotdf["mid_time"] = plotdf.open_time + timeinterval / 2

        return ColumnDataSource(plotdf)

    def __post_init__(self):
        # Here we follow binance format and enforce proper python types
        if "open_time" in self.df.columns:
            # setting open_time as index, popping to avoid ambiguity, and ordering (required for slicing !)
            self.df.set_index(
                pd.DatetimeIndex(
                    data=self.df.pop("open_time"),
                    dtype=PriceCandle.as_dtype()["open_time"],
                ),
                inplace=True,
            )
        # else we assume index is already the open_time...

        # always sort it, just in case
        self.df.sort_index(inplace=True)

        # TODO : assert proper dataframe format of columns...

    def __eq__(self, other: _OHLCFrame) -> bool:
        assert isinstance(
            other, _OHLCFrame
        )  # in our design the type infers the columns.
        if self is other:
            # here we follow python on equality https://docs.python.org/3.6/reference/expressions.html#id12
            return True
        elif len(self) == len(other):
            # BEWARE : https://github.com/pandas-dev/pandas/issues/20442
            for s, o in zip(self, other):  # this iterates and cast to PriceCandle
                if s != o:  # here we use PriceCAndle.__eq__ !
                    break
            else:
                return True
        else:
            return False

    def __getitem__(
        self, item: Union[datetime, slice]
    ) -> Union[_OHLCFrame, PriceCandle]:
        if isinstance(item, slice):
            # dataframe slice handled by pandas boolean indexer
            try:
                return _OHLCFrame(
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
                    & (item < self.df.close_time.astype(dtype="datetime64[us]"))
                ]
                # This implies index unicity and non-overlapping of time intervals...
                if len(rs) == 1:
                    return PriceCandle(
                        **rs.reset_index(drop=False).iloc[0]
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

    def __len__(self):
        return len(self.df)

    # Ref : https://docs.python.org/3.8/library/stdtypes.html#set.intersection
    def intersection(self, other: _OHLCFrame):
        # extracting candles when there is *exact* equality
        candles = []
        # very naive implementation. TODO : optimize
        # REMINDER : this is just a set of candle, no candle merging.
        for t in self:
            if t in other:
                candles.append(t)

        return _OHLCFrame.from_candleslist(*candles)

    def __str__(self):
        # optimize before display (high decimal precision is not manageable by humans)
        optdf = self.optimized()
        return tabulate(optdf, headers="keys", tablefmt="psql")

    def optimized(self) -> pd.DataFrame:
        opt_copy = self.df.copy(deep=True)
        opt_copy.convert_dtypes()
        return opt_copy


@dataclass(frozen=True)
class OHLCMinute(_OHLCFrame, interval=TimeInterval.minutely):
    @st.composite
    @staticmethod
    def strategy(
        draw,
        min_size=1,
        max_size=5,
    ):
        # TODO: get this from _OHLCFrame strategy...
        ots = draw(
            st.datetimes(  # no need to be extra precise on max bound here
                min_value=datetime(year=MINYEAR, month=1, day=1),
                max_value=datetime(year=MAXYEAR, month=12, day=31)
                - TimeInterval.minutely.to_timedelta(),
            ),
        )

        # generating candles (no time just yet)
        cdl = draw(
            st.lists(
                elements=PriceCandle.strategy(), min_size=min_size, max_size=max_size
            )
        )

        timed = []
        cts = ots
        for c in cdl:
            timed.append(MinutePriceCandle(open_time=cts, price_=c))
            cts = cts + TimeInterval.minutely.to_timedelta()

        return OHLCMinute.from_candleslist(*timed)

    def __iter__(self):
        # we need to drop the index to recover 'open_time' field in tuple with proper name
        for t in self.df.reset_index(drop=False).itertuples(index=False):
            yield MinutePriceCandle(**t._asdict())

    def __contains__(self, item: Union[MinutePriceCandle, datetime]) -> bool:
        # https://docs.python.org/2/reference/datamodel.html#object.__contains__
        if isinstance(item, MinutePriceCandle):
            for t in self:  # iterates and cast to PriceCandle
                if t == item:  # using Trade equality
                    return True
            return False
        elif isinstance(item, datetime):  # continuous index
            for t in self:
                # Note : same semantics as getitem
                if (
                    t.open_time <= item < t.close_time
                ):  # checking one candle contains the datetime
                    return True
            return False
        else:
            return False

    # Ref : https://docs.python.org/3.8/library/stdtypes.html#set.union
    def merge(self, other: OHLCMinute):

        # TODO : not resetting index if we can avoid it. but merge seems to have a problem with indexes...
        newdf_noidx = merge_ordered(
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
            if chosen.get("open_time", None) != row[
                "open_time"
            ] or (  # no chosen, or different index => take new row  # same index : we need to compare rows on num_trades, volume, high and low
                chosen["num_trades"] < row["num_trades"]
                or chosen["volume"] < row["volume"]
                # careful with strictness when comparing high and low bounds...
                or (chosen["high"] < row["high"] and chosen["low"] >= row["low"])
                or (chosen["high"] <= row["high"] and chosen["low"] > row["low"])
            ):  # in that case pick the new row
                chosen = row.copy()
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
        return _OHLCFrame(df=newdf)

    # Ref : https://docs.python.org/3.8/library/stdtypes.html#set.difference
    def difference(self, other: OHLCMinute):
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

        return _OHLCFrame.from_candleslist(*candles)


@dataclass(frozen=True)
class OHLCHourly(_OHLCFrame):
    pass


@dataclass(frozen=True)
class OHLCDaily(_OHLCFrame):
    pass


@dataclass(frozen=True)
class OHLCWeekly(_OHLCFrame):
    pass


if __name__ == "__main__":
    print(OHLCMinute.strategy().example())
    # print(OHLCHourly.strategy().example())
    # print(OHLCDaily.strategy().example())
    # print(OHLCWeekly.strategy().example())

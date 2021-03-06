from __future__ import annotations

from dataclasses import fields
from datetime import MAXYEAR, MINYEAR, datetime, timedelta, timezone
from decimal import Decimal
from typing import Dict, Iterable, Optional, Union

import hypothesis.strategies as st
import numpy as np
import pandas as pd
from hypothesis.strategies import SearchStrategy
from pydantic import validator
from pydantic.dataclasses import dataclass

# Leveraging pydantic to validate based on type hints


@dataclass(eq=False)
class PriceCandle:
    # REMINDER : as 'precise' and 'pythonic' semantic as possible
    open_time: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    close_time: datetime
    qav: Decimal
    num_trades: int
    taker_base_vol: Decimal
    taker_quote_vol: Decimal
    is_best_match: int  # ??

    # IMPORTANT: a Price Candle seems to be made of three main parts, each with different behavior:
    # - time bounds
    #   needs to be somewhat parameterized by a "list of pricecandles", constant interval, no overlaps, etc.
    # - price candle itself (ohlc)
    #   there is an order relation here that helps use merging different candle in same timebounds
    # - volume & specific binance stuff
    #   other exchange will have different useful things here (kraken's vwap f.i.)
    #
    # These should probably be split into different classes if optimizing becomes necessary (numpy f.i.)
    # and then "transparently" joined (think categorical product) into a Binance PriceCandle...

    @validator("open_time", "close_time", pre=True)
    def convert_pandas_timestamp(cls, v: Union[pd.Timestamp, datetime]):
        if isinstance(v, pd.Timestamp):
            v = v.to_pydatetime(warn=False)  # silently ignoring nanoseconds

        if isinstance(v, np.datetime64):  # Ref: https://stackoverflow.com/a/13704307
            td = (
                v.astype("datetime64[us]")
                - np.datetime64("1970-01-01T00:00:00.000000", "us")
            ).astype(timedelta)
            v = datetime.utcfromtimestamp(td.total_seconds())
            # TODO : this implies float computation (innacurate after 2117).
            #  To detect, remove __eq__ to retrieve exact eq from dataclass => convert to int computation only

        if isinstance(v, datetime):
            if (
                v.tzinfo is None
            ):  # None implies UTC (CAREFUL: for base python, local is implied in this case !)
                return v.replace(tzinfo=timezone.utc)
            else:
                return v.astimezone(tz=timezone.utc)

        return v

    @classmethod  # actually property of the class itself -> metaclass (see datacrystals...)
    def as_dtype(cls) -> Dict[str, np.dtype]:
        """ Interpretation of this dataclass as dtype for optimizations with numpy """
        # Ref : https://numpy.org/devdocs/reference/arrays.dtypes.html#arrays-dtypes-constructing
        specified = {
            "open_time": np.dtype("datetime64[ns]"),
            "close_time": np.dtype("datetime64[ns]"),
            # CAREFUL : timezone naive since numpy 1.11.0
            # Note: datetime64[ms] is usual server timestamp, but not enough precise for python [us]
            # Note: datetime64[ns] is the enforced format for pandas datetime/timestamp, but more precise than python [us]
            # CAREFUL : pandas might erroneously select int64 here...
            "num_trades": np.dtype("uint64"),
            "is_best_match": np.dtype("uint64"),
        }
        # TODO : min/max properties on the type itself...

        # CAREFUL order needs to match fields order here...
        return {
            f.name: specified[f.name] if f.name in specified else np.dtype("O")
            for f in fields(cls)
        }

    # Strategies, inferring attributes from type hints by default
    @st.composite
    @staticmethod
    def strategy(
        draw,
        time_deltas: SearchStrategy = st.timedeltas(
            min_value=timedelta(microseconds=1),
            max_value=timedelta(
                days=100
            ),  # no point being too optimistic, there are various limitations in timing implementations...
        ),
        timebounds: Optional[SearchStrategy] = None,
    ):  # TODO : maybe we should split the time and the candle dimensions here...
        if timebounds is None:
            timebounds = time_deltas.flatmap(
                lambda td: st.datetimes(  # no need to be extra precise on max bound here, but we need to deal with pandas&python limitations...
                    min_value=max(
                        datetime(year=MINYEAR, month=1, day=1),
                        pd.to_datetime(pd.Timestamp.min),
                    ),
                    max_value=min(
                        datetime(year=MAXYEAR, month=12, day=31),
                        pd.to_datetime(pd.Timestamp.max),
                    )
                    - td,
                ).flatmap(
                    lambda otd: st.tuples(st.just(otd), st.just(otd + td))
                )
            )

        timebounds = draw(timebounds)

        # we need some coherence in ohlc values
        ohlc = draw(
            st.tuples(
                st.decimals(allow_nan=False, allow_infinity=False),
                st.decimals(allow_nan=False, allow_infinity=False),
            ).flatmap(
                lambda x: st.tuples(
                    st.just(x[0]),  # open
                    st.decimals(
                        min_value=max(x[0], x[1]), allow_nan=False, allow_infinity=False
                    ),  # high
                    st.decimals(
                        max_value=min(x[0], x[1]), allow_nan=False, allow_infinity=False
                    ),  # low
                    st.just(x[1]),  # close
                )
            )
        )

        open = ohlc[0]
        high = ohlc[1]
        low = ohlc[2]
        close = ohlc[3]

        npii = np.iinfo(np.uint64)

        return PriceCandle(
            open_time=timebounds[0],
            open=open,
            high=high,
            low=low,
            close=close,
            volume=draw(
                st.decimals(allow_nan=False, allow_infinity=False, min_value=Decimal(0))
            ),
            close_time=timebounds[1],
            qav=draw(
                st.decimals(allow_nan=False, allow_infinity=False, min_value=Decimal(0))
            ),
            num_trades=draw(st.integers(min_value=npii.min, max_value=npii.max)),
            taker_base_vol=draw(
                st.decimals(allow_nan=False, allow_infinity=False, min_value=Decimal(0))
            ),
            taker_quote_vol=draw(
                st.decimals(allow_nan=False, allow_infinity=False, min_value=Decimal(0))
            ),
            # we need to bound this into supported numpy range, otherwise value will change when stored into a dataframe
            # BUG on       12532440469543193200
            # uint64.max : 18446744073709551615
            is_best_match=draw(st.integers(min_value=npii.min, max_value=npii.max)),
        )

    def __eq__(self, other):
        for f in fields(self):
            if (
                f.type == "datetime"
            ):  # special comparison for datetime (resolution is important here...)
                s = getattr(self, f.name)
                o = getattr(other, f.name)
                delta = s - o if s >= o else o - s  # absolute delta
                # we need to take in account resolution to avoid python precision issues
                if delta > max(
                    getattr(self, f.name).resolution, getattr(other, f.name).resolution
                ):
                    return False
            elif getattr(self, f.name) != getattr(other, f.name):
                return False
        return True

    def __str__(self) -> str:
        return f"""
open_time: {self.open_time}
open: {self.open}
high: {self.high}
low: {self.low}
close: {self.close}
volume: {self.volume}
close_time: {self.close_time}
qav: {self.qav}
num_trades: {self.num_trades}
taker_base_vol: {self.taker_base_vol}
taker_quote_vol: {self.taker_quote_vol}
is_best_match: {self.is_best_match}
"""

    def __dir__(self) -> Iterable[str]:
        # hiding private methods and data validators
        return [f.name for f in fields(self)]


if __name__ == "__main__":
    print(PriceCandle.strategy().example())

from __future__ import annotations

from dataclasses import fields
from datetime import MAXYEAR, MINYEAR, datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Dict, Iterable, Optional, Union

import hypothesis.strategies as st
import numpy as np
import pandas as pd
from pydantic import validator
from pydantic.dataclasses import dataclass

# Leveraging pydantic to validate based on type hints


class TimeInterval(Enum):
    minutely = "1m"
    minutely_3 = "3m"
    minutely_5 = "5m"
    minutely_15 = "15m"
    minutely_30 = "30m"
    hourly = "1h"
    hourly_2 = "2h"
    hourly_4 = "4h"
    hourly_6 = "6h"
    hourly_8 = "8h"
    hourly_12 = "12h"
    daily = "1d"
    daily_3 = "3d"
    weekly = "1w"

    # monthly = "1M"  # DROPPED

    def to_timedelta(self):
        return {
            "1m": timedelta(minutes=1),
            "3m": timedelta(minutes=3),
            "5m": timedelta(minutes=5),
            "15m": timedelta(minutes=15),
            "30m": timedelta(minutes=30),
            "1h": timedelta(hours=1),
            "2h": timedelta(hours=2),
            "4h": timedelta(hours=4),
            "6h": timedelta(hours=6),
            "8h": timedelta(hours=8),
            "12h": timedelta(hours=12),
            "1d": timedelta(days=1),
            "3d": timedelta(days=3),
            "1w": timedelta(weeks=1),
            # '1M': timedelta(months)  # DROPPING MONTHLY Candle features (probably not useful for us)
        }[self.value]


@dataclass(frozen=True, init=True)
class PriceCandle:
    # REMINDER : as 'precise' and 'pythonic' semantic as possible

    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    qav: Decimal
    num_trades: int
    taker_base_vol: Decimal
    taker_quote_vol: Decimal
    is_best_match: Decimal  # ??

    # Strategies, inferring attributes from type hints by default
    @st.composite
    @staticmethod
    def strategy(  # CAREFUL different order here given composite behavior : adding draw arg in first position
        draw,  # This messes up a lot of tooling...
    ):
        # we need some coherence in ohlc values
        open = draw(st.decimals(allow_nan=False, allow_infinity=False))
        close = draw(st.decimals(allow_nan=False, allow_infinity=False))
        high = draw(
            st.decimals(
                min_value=min(open, close), allow_nan=False, allow_infinity=False
            )
        )
        low = draw(
            st.decimals(
                min_value=max(open, close), allow_nan=False, allow_infinity=False
            )
        )

        npii = np.iinfo(np.uint64)

        return PriceCandle(
            open=open,
            high=high,
            low=low,
            close=close,
            volume=draw(
                st.decimals(allow_nan=False, allow_infinity=False, min_value=Decimal(0))
            ),
            qav=draw(
                st.decimals(allow_nan=False, allow_infinity=False, min_value=Decimal(0))
            ),
            num_trades=draw(st.integers(min_value=npii.min, max_value=npii.max)),
            taker_base_vol=draw(
                st.decimals(allow_nan=False, allow_infinity=False, min_value=0)
            ),
            taker_quote_vol=draw(
                st.decimals(allow_nan=False, allow_infinity=False, min_value=0)
            ),
            is_best_match=draw(
                st.decimals(allow_nan=False, allow_infinity=False, min_value=0)
            ),
        )

    @classmethod  # actually property of the class itself -> metaclass (see datacrytals...)
    def as_dtype(cls) -> Dict[str, np.dtype]:
        """ Interpretation of this dataclass as dtype for optimizations with numpy """
        # Ref : https://numpy.org/devdocs/reference/arrays.dtypes.html#arrays-dtypes-constructing
        specified = {
            "num_trades": np.dtype("uint64")
            # CAREFUL : timezone naive since numpy 1.11.0
            # Note: datetime64[ms] is usual server timestamp, but not enough precise for python [us]
            # Note: datetime64[ns] is the enforced format for pandas datetime/timestamp, but more precise than python [us]
        }
        # TODO : min/max properties on the type itself...
        # TODO : more strict column dtypes !

        # CAREFUL order needs to match fields order here...
        return {
            f.name: specified[f.name] if f.name in specified else np.dtype("O")
            for f in fields(cls)
        }

    def __str__(self) -> str:
        # simple string display to avoid special cases
        return "\n".join(
            f"{f.name}: {str(getattr(self, f.name))}" for f in fields(self)
        )

    def __dir__(self) -> Iterable[str]:
        # hiding private methods and data validators
        return [f.name for f in fields(self)]

    # TODO : some kind of binary operation (tensor product ?) that will chose one candle
    #  as "more accurate"/"containing more info" compared to the other one
    #  only valid for same timeframe (otherwise would return an ohlcframe)
    #  OR maybe this is a union of candles ??
    # This is aimed to be used when merging two list of candles (see ohlcframe...)
    # TODO : same thing for the difference...

    # Note : we get candles directly from server, there might not be any guarantees when merging candles...
    # maybe is it more about choosing one ?? Maybe we have an order on candles ??

    def __lt__(self, other: PriceCandle):
        # making sure they are of the same type # TODO : better way ??
        assert isinstance(other, type(self))

        return (
            self.num_trades < other.num_trades
            or self.volume < other.volume
            # careful with strictness (and precision) when comparing high and low bounds...
            or (self.high < other.high and self.low >= other.low)
            or (self.high <= other.high and self.low > other.low)
        )

    def __gt__(self, other: PriceCandle):
        # making sure they are of the same type # TODO : better way ??
        assert isinstance(other, type(self))

        return (
            self.num_trades > other.num_trades
            or self.volume > other.volume
            # careful with strictness (and precision) when comparing high and low bounds...
            or (self.high > other.high and self.low <= other.low)
            or (self.high >= other.high and self.low < other.low)
        )


@dataclass(frozen=True, init=False)
class _TimedCandle:
    open_time: datetime
    close_time: datetime
    # Delegate to PriceCandle, because we deal with different subtleties via class inheritance...
    price_: PriceCandle

    @property
    def open(self):
        return self.price_.open

    @property
    def high(self):
        return self.price_.high

    @property
    def low(self):
        return self.price_.low

    @property
    def close(self):
        return self.price_.close

    @property
    def volume(self):
        return self.price_.volume

    @property
    def qav(self):
        return self.price_.qav

    @property
    def num_trades(self):
        return self.price_.num_trades

    @property
    def taker_base_vol(self):
        return self.price_.taker_base_vol

    @property
    def taker_quote_vol(self):
        return self.price_.taker_quote_vol

    # Should not use (as per docs...)
    # @property
    # def is_best_match(self):
    #     return self.price_.is_best_match

    @validator("open_time", "close_time", pre=True)
    def convert_pandas_timestamp(cls, v: Union[datetime, pd.Timestamp]):
        if isinstance(v, pd.Timestamp):
            return v.to_pydatetime()
        return v

    def __init_subclass__(
        cls, interval: TimeInterval = TimeInterval.minutely, **kwargs
    ):
        super().__init_subclass__(**kwargs)
        print(f"Called __init_subclass__({cls}, {interval})")
        cls.interval = interval

    @classmethod
    def strategy(  # CAREFUL different order here given composite behavior : adding draw arg in first position
        cls,  # This messes up a lot of tooling...
    ):
        # CAREFUL: datetime min and max are different for computation
        # see supported Operations https://docs.python.org/3/library/datetime.html#datetime-objects
        ots = st.datetimes(  # no need to be extra precise on max bound here
            min_value=datetime(year=MINYEAR, month=1, day=1),
            max_value=datetime(year=MAXYEAR, month=12, day=31)
            - cls.interval.to_timedelta(),
        )

        return st.builds(cls, open_time=ots, price_=PriceCandle.strategy())

    @classmethod  # actually property of the class itself -> metaclass (see datacrytals...)
    def as_dtype(cls) -> Dict[str, np.dtype]:
        """ Interpretation of this dataclass as dtype for optimizations with numpy """
        # Ref : https://numpy.org/devdocs/reference/arrays.dtypes.html#arrays-dtypes-constructing
        specified = {
            "open_time": np.dtype("datetime64[ns]"),
            "close_time": np.dtype("datetime64[ns]"),
            # CAREFUL : timezone naive since numpy 1.11.0
            # Note: datetime64[ms] is usual server timestamp, but not enough precise for python [us]
            # Note: datetime64[ns] is the enforced format for pandas datetime/timestamp, but more precise than python [us]
        }
        # TODO : min/max properties on the type itself...
        # TODO : more strict column dtypes !

        # returning dtype MERGED with price candle

        return {**specified, **PriceCandle.as_dtype()}

    def __init__(
        self,
        open_time: datetime,
        close_time: Optional[datetime] = None,
        price_: Optional[PriceCandle] = None,
        **kwargs,
    ):
        object.__setattr__(self, "open_time", open_time)

        if close_time is not None:
            # forcing value (maybe we should assert instead ?)
            object.__setattr__(self, "close_time", close_time)
        else:
            object.__setattr__(
                self, "close_time", open_time + self.interval.to_timedelta()
            )

        # If there is price_ we take it as such, else we attempt to build a Candle
        if price_ is not None:
            object.__setattr__(self, "price_", price_)
        else:
            object.__setattr__(self, "price_", PriceCandle(**kwargs))

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
        """

    def __dir__(self) -> Iterable[str]:
        # hiding private methods and data validators
        return [
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
        ]


@dataclass(frozen=True, init=False)
class MinutePriceCandle(_TimedCandle, interval=TimeInterval.minutely):
    def __init__(
        self,
        open_time: datetime,
        close_time: Optional[datetime] = None,
        price_: Optional[PriceCandle] = None,
        **kwargs,
    ):
        super(MinutePriceCandle, self).__init__(
            open_time=open_time, close_time=close_time, price_=price_, **kwargs
        )

    def __lt__(self, other: MinutePriceCandle):
        if self.open_time == other.open_time and self.close_time == other.close_time:
            return self.price_ < other.price_
        else:
            return None  # comparison of two candles when time bounds dont match doesnt mean anything.

    def __gt__(self, other: MinutePriceCandle):
        if self.open_time == other.open_time and self.close_time == other.close_time:
            return self.price_ > other.price_
        else:
            return None  # comparison of two candles when time bounds dont match doesnt mean anything.


@dataclass(frozen=True, init=False)
class HourlyPriceCandle(_TimedCandle, interval=TimeInterval.hourly):
    def __init__(
        self,
        open_time: datetime,
        close_time: Optional[datetime] = None,
        price_: Optional[PriceCandle] = None,
        **kwargs,
    ):
        super(HourlyPriceCandle, self).__init__(
            open_time=open_time, close_time=close_time, price_=price_, **kwargs
        )

    def __lt__(self, other: HourlyPriceCandle):
        if self.open_time == other.open_time and self.close_time == other.close_time:
            return self.price_ < other.price_
        else:
            return None  # comparison of two candles when time bounds dont match doesnt mean anything.

    def __gt__(self, other: HourlyPriceCandle):
        if self.open_time == other.open_time and self.close_time == other.close_time:
            return self.price_ > other.price_
        else:
            return None  # comparison of two candles when time bounds dont match doesnt mean anything.


@dataclass(frozen=True, init=False)
class DailyPriceCandle(_TimedCandle, interval=TimeInterval.daily):
    def __init__(
        self,
        open_time: datetime,
        close_time: Optional[datetime] = None,
        price_: Optional[PriceCandle] = None,
        **kwargs,
    ):
        super(DailyPriceCandle, self).__init__(
            open_time=open_time, close_time=close_time, price_=price_, **kwargs
        )

    def __lt__(self, other: DailyPriceCandle):
        if self.open_time == other.open_time and self.close_time == other.close_time:
            return self.price_ < other.price_
        else:
            return None  # comparison of two candles when time bounds dont match doesnt mean anything.

    def __gt__(self, other: DailyPriceCandle):
        if self.open_time == other.open_time and self.close_time == other.close_time:
            return self.price_ > other.price_
        else:
            return None  # comparison of two candles when time bounds dont match doesnt mean anything.


@dataclass(frozen=True, init=False)
class WeeklyPriceCandle(_TimedCandle, interval=TimeInterval.weekly):
    def __init__(
        self,
        open_time: datetime,
        close_time: Optional[datetime] = None,
        price_: Optional[PriceCandle] = None,
        **kwargs,
    ):
        super(WeeklyPriceCandle, self).__init__(
            open_time=open_time, close_time=close_time, price_=price_, **kwargs
        )

    def __lt__(self, other: WeeklyPriceCandle):
        if self.open_time == other.open_time and self.close_time == other.close_time:
            return self.price_ < other.price_
        else:
            return None  # comparison of two candles when time bounds dont match doesnt mean anything.

    def __gt__(self, other: WeeklyPriceCandle):
        if self.open_time == other.open_time and self.close_time == other.close_time:
            return self.price_ > other.price_
        else:
            return None  # comparison of two candles when time bounds dont match doesnt mean anything.


if __name__ == "__main__":
    print(MinutePriceCandle.strategy().example())
    print(HourlyPriceCandle.strategy().example())
    print(DailyPriceCandle.strategy().example())
    print(WeeklyPriceCandle.strategy().example())

from __future__ import annotations

from datetime import datetime, timedelta
from enum import Enum
from typing import ClassVar, Dict, Optional, Union

import portion
from portion import Interval


# TODO: get rid of that, TimeStep will do the job
class TimeIntervalEnum(Enum):
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


class TimeIntervalDelta(Enum):
    minutely = timedelta(minutes=1)
    minutely_3 = timedelta(minutes=3)
    minutely_5 = timedelta(minutes=5)
    minutely_15 = timedelta(minutes=15)
    minutely_30 = timedelta(minutes=30)
    hourly = timedelta(hours=1)
    hourly_2 = timedelta(hours=2)
    hourly_4 = timedelta(hours=4)
    hourly_6 = timedelta(hours=6)
    hourly_8 = timedelta(hours=8)
    hourly_12 = timedelta(hours=12)
    daily = timedelta(days=1)
    daily_3 = timedelta(days=3)
    weekly = timedelta(weeks=1)

    def __lt__(self, other: TimeIntervalDelta):
        return self.value < other.value

    def __gt__(self, other: TimeIntervalDelta):
        return self.value > other.value


# TODO : get rid of this, TimeStep willl do the job
def timeinterval_to_timedelta(self):
    # timedelta conversion
    _convert: ClassVar = {
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
    }
    return _convert[self.value]


# TODO: get rid of that, TimeStep will do the job
def timeinterval_from_timedelta(td: timedelta):
    # timedelta conversion
    _convert: ClassVar = {
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
    }
    for k, v in _convert.items():
        if v >= td:
            return k


class TimeStep:

    _api_convert: ClassVar[Dict[TimeIntervalDelta, str]] = {
        TimeIntervalDelta.minutely: "1m",
        TimeIntervalDelta.minutely_3: "3m",
        TimeIntervalDelta.minutely_5: "5m",
        TimeIntervalDelta.minutely_15: "15m",
        TimeIntervalDelta.minutely_30: "30m",
        TimeIntervalDelta.hourly: "1h",
        TimeIntervalDelta.hourly_2: "2h",
        TimeIntervalDelta.hourly_4: "4h",
        TimeIntervalDelta.hourly_6: "6h",
        TimeIntervalDelta.hourly_8: "8h",
        TimeIntervalDelta.hourly_12: "12h",
        TimeIntervalDelta.daily: "1d",
        TimeIntervalDelta.daily_3: "3d",
        TimeIntervalDelta.weekly: "1w",
    }

    delta: TimeIntervalDelta

    def __init__(self, step: Optional[Union[TimeIntervalDelta, timedelta]] = None):

        if isinstance(step, TimeIntervalDelta):
            self.delta = step
        elif step is None:
            self.delta = TimeIntervalDelta.minutely
        elif isinstance(step, timedelta):
            # find closest TimeIntervalDelta
            closest = TimeIntervalDelta.minutely
            for tid in TimeIntervalDelta:
                if tid.value > step:
                    # if we passed step
                    if (tid.value - step) < step - closest.value:
                        # if tid is closer to step, we pick that one
                        closest = tid
                    # we are done
                    break
                closest = tid

            self.delta = closest
        else:
            RuntimeError(f"Cannot convert {step} to a TimeStep")

    def __hash__(self):
        """only the delta attribute is useful. This class is merely a conversion convenience.
        As a side-effect, TimeStep is equal to TimeIntervalDelta with same delta value
        """
        return hash(self.delta)

    def __eq__(self, other: TimeStep):
        """equality follows hashing"""
        return hash(self) == hash(other)

    def __lt__(self, other: Union[TimeStep, TimeIntervalDelta, timedelta]):
        if isinstance(other, TimeStep):
            return self.delta < other.delta
        elif isinstance(other, TimeIntervalDelta):
            return self.delta < other
        elif isinstance(other, timedelta):
            return self.delta.value < other
        else:
            return None  # anything else is probably not comparable

    def __gt__(self, other: Union[TimeStep, TimeIntervalDelta, timedelta]):
        if isinstance(other, TimeStep):
            return self.delta > other.delta
        elif isinstance(other, TimeIntervalDelta):
            return self.delta > other
        elif isinstance(other, timedelta):
            return self.delta.value > other
        else:
            return None  # anything else is probably not comparable

    def __repr__(self):  # TODO : parsing both ways (useful for bokeh)
        return str(self.delta.value)

    def __str__(self):
        return self.to_api()

    def to_api(self) -> str:
        return self._api_convert[self.delta]


class TimeInterval:
    # New class to manipulate time intervals

    interval: Interval  # TODO: [datetime]
    step: Optional[TimeStep]

    @property
    def start(self):
        return self.interval.lower

    @property
    def stop(self):
        return self.interval.upper

    def __init__(
        self,
        interval: Optional[Interval] = None,  # TODO : only one way to create this
        start: Optional[datetime] = None,
        stop: Optional[datetime] = None,
        step: Optional[Union[TimeStep, timedelta]] = None,
    ):
        self.interval = (
            portion.closed(start, stop)
            if interval is None and start is not None and stop is not None
            else interval
        )
        self.step = (
            None
            if step is None
            else step
            if isinstance(step, TimeStep)
            else TimeStep(step)
        )

    def __iter__(self):
        portion.iterate(self.interval, step=self.step)

    def union(self, other: TimeInterval):

        assert self.step == other.step  # TODO : pass this in types instead ??
        if self.interval is None:
            return other
        elif other.interval is None:
            return self
        else:
            return TimeInterval(interval=self.interval | other.interval, step=self.step)

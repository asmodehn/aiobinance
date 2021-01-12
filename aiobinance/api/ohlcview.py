from __future__ import annotations

import asyncio
from asyncio import AbstractEventLoop, Queue, Task
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, List, Optional, Union

import hypothesis.strategies as st

from aiobinance.api.model.ohlcframe import OHLCFrame
from aiobinance.api.model.pricecandle import PriceCandle
from aiobinance.api.model.timeinterval import (
    TimeInterval,
    TimeStep,
    timeinterval_from_timedelta,
)
from aiobinance.api.model.trade import Trade
from aiobinance.api.pure.ohlcviewbase import OHLCViewBase
from aiobinance.api.rawapi import Binance

# TODO: this should probably done in types instead (metaclass, etc.)
_ohlcview_instances: Dict[str, OHLCView] = {}

# TODO : request sent to this module (or each possible instance)
# should be done here (globally in module -> unique in sys.modules)
# pbm : it is symbol dependent...


class OHLCView(OHLCViewBase):
    """ A 'passively mutating' list of candles """

    api: Binance
    symbol: Optional[str]

    # TODO : aiostream instead of queue here ?
    #  we need to think about combining expectatinos in a way that make sense (Time Interval arithmetic)
    expectations: Optional[Queue]  # containing TimeInterval as the requested dataset

    update_hooks: Dict[TimeStep, List[Callable[[OHLCFrame], bool]]]
    update_loop: Optional[Task]

    @st.composite
    @staticmethod
    def strategy(draw, max_size=5):
        frames = draw(st.lists(OHLCFrame.strategy(), max_size=max_size))
        return OHLCView(api=Binance(), symbol=draw(st.text(max_size=5)), *frames)

    def __new__(cls, api: Binance = Binance(), symbol: Optional[str] = None, *frames):

        if symbol in _ohlcview_instances.keys():
            return _ohlcview_instances[
                symbol
            ]  # to have only one instance for all data.

        self = super(OHLCView, cls).__new__(cls)
        # One running loop per symbol, and only one instance !
        _ohlcview_instances[symbol] = self
        return self  # init will do the rest

    def __init__(self, api: Binance = Binance(), symbol: Optional[str] = None, *frames):
        self.api = api
        self.symbol = symbol

        self.expectations = None  # maybe no async event loop just yet
        self.update_hooks = {}  # because multiple things can wait for one update
        self.update_loop = None

        super(OHLCView, self).__init__(*frames)

    def update_hook(self, ts: TimeStep, callback: Callable[[OHLCFrame], Any]):
        self.update_hooks.setdefault(ts, [])
        self.update_hooks[ts].append(callback)

    async def request(  # Note : keep this async, for when we ll move to an async API
        self,
        start_time: Optional[datetime] = None,
        stop_time: Optional[datetime] = None,
        interval: Optional[TimeStep] = None,
    ):
        """ this retrieves price ohlcv data"""

        if interval is None:
            # make request for one timeframe already present in self.frames
            if stop_time is None:  # means "until now"
                # takes smallest timeframe that doesn't have recent data
                useful_tfs = [
                    tf
                    for tf, f in self.frames
                    if f.close_time is None or stop_time > f.close_time
                ]
                interval = min(useful_tfs) if useful_tfs else None
                # stop_time remains None, to use binance API default
            else:
                # takes biggest timeframe that doesnt have past data
                useful_tfs = [
                    tf
                    for tf, f in self.frames.items()
                    if f.open_time is None or stop_time < f.open_time
                ]
                interval = max(useful_tfs) if useful_tfs else None

        # Interval might still be none, but we should examine start and stop time first...

        if start_time is not None:
            # to make sure the timezone is set at this stage (otherwise timestamps will be ambiguous)
            assert start_time.tzinfo is not None
            start_timestamp = int(start_time.timestamp() * 1000)
        else:
            start_timestamp = None
        if stop_time is not None:
            assert stop_time.tzinfo is not None
            stop_timestamp = int(stop_time.timestamp() * 1000)
        else:
            stop_timestamp = None

        # Interval might still be None !
        if interval is None:
            if start_time is not None and stop_time is not None:
                # special case to implicitely override default...
                interval = self.api.interval(start_timestamp, stop_timestamp)
            else:
                interval = "1m"  # Hardcoded DEFAULT
        else:  # convert TimeStep to meaningful interval for binance API
            interval = interval.to_api()
            # Note: this should error when we dont have a TimeStep -> request param will be wrong

        # choosing which arguments to pass to rely on binance default behavior (is it a good idea ?)
        req_args = {}
        if interval is not None:
            req_args.update({"interval": interval})
        if start_timestamp is not None:
            req_args.update({"startTime": start_timestamp})
        if stop_timestamp is not None:
            req_args.update({"endTime": stop_timestamp})

        res = self.api.call_api(
            command="klines",
            symbol=self.symbol,
            **req_args,
            limit=1000,  # TODO: maybe some clever pagination system should be handled in API side...
        )

        if res.is_ok():
            res = res.value
        else:
            raise RuntimeError(res.err())

        # Binance translation is only a matter of binance json -> python data structure && avoid data duplication.
        # We do not want to change the semantics of the exchange exposed models here.
        candles = [
            PriceCandle(
                open_time=r[0],
                open=r[1],
                high=r[2],
                low=r[3],
                close=r[4],
                volume=r[5],
                close_time=r[6],
                qav=r[7],
                num_trades=r[8],
                taker_base_vol=r[9],
                taker_quote_vol=r[10],
                is_best_match=r[11],
            )
            for r in res
        ]

        frame = OHLCFrame.from_candleslist(*candles)

        # We let base class handle merging or replacing ohlcframes depending on interval
        return super(OHLCView, self).__call__(frame=frame)

    async def loop(self, mini_sleep: timedelta = timedelta(seconds=3)):

        if self.expectations is None:
            self.expectations = Queue()

        # TODO : avoid multiple calls here !!
        if not self.expectations.empty():  # to avoid blocking when not useful
            tint = await self.expectations.get()

            try:
                # TODO : schedule requests and balance optimization with accuracy
                #  multiple request might improve results (seen with kraken at least)
                await self.at(
                    timestep=tint.step, start_time=tint.start, stop_time=tint.stop
                )
            except Exception:
                raise
            finally:  # to be sure we mark this task as done and we can keep working...
                self.expectations.task_done()

        await asyncio.sleep(
            mini_sleep.total_seconds()
        )  # minisleep to avoid looping too fast.

        # this trampoline and behaves as a minimal inner service...
        self.update_loop = asyncio.get_running_loop().create_task(
            self.loop(mini_sleep=mini_sleep)
        )

        # we return after first process, while leaving a task running when possible...
        # TODO:investigate if trio might be better here for structured async concurrency...

    async def run(self, mini_sleep: timedelta = timedelta(seconds=3)):
        if self.update_loop is None:
            await self.loop(mini_sleep=mini_sleep)
        # else we silently skip it because we ever want only ONE loop !

    async def at(
        self,
        timestep: TimeStep,
        start_time: Optional[datetime] = None,
        stop_time: Optional[datetime] = None,
    ):
        """
        :param timestep: the timestep to access, and for which to retrieve data if needed
        :param start_time: the start_time of data we need to retrieve (might not be returned, use [] to access it if needed)
        :param stop_time: the stop_time of data we need to retrieve (might not be returned, use [] to access it if needed)
        :return:
        """
        if (
            timestep not in self.frames
            or (self.frames[timestep].empty)
            or (start_time is not None and self.frames[timestep].open_time > start_time)
            or (stop_time is not None and self.frames[timestep].close_time < stop_time)
        ):
            # keep old version
            # Note : for this to work, this must be the only point where it is possible to update the encapsulated data
            old_frame = self.frames[timestep]

            # do the first request to get recent data, and await
            await self.request(
                start_time=start_time, stop_time=stop_time, interval=timestep
            )

            # broadcast update
            # TODO : OPTIMIZE THIS ! Difference Computation is too slow...
            frameupdate = self.frames[timestep].difference(old_frame)
            # NEW WAY
            if not frameupdate.empty:
                for hook in self.update_hooks[timestep]:
                    hook(frameupdate)
                    # TODO : somethg useful with return value ? popping the hook ?

        # return the frame
        return self.frames[timestep]


if __name__ == "__main__":
    from aiobinance.config import load_api_keyfile

    api = Binance(credentials=load_api_keyfile())
    tv = OHLCView(api=api, symbol="COTIBNB")

    # async just because main is sync and cannot block/await
    async def access_data():
        start_time = datetime.fromtimestamp(1598524340551 / 1000, tz=timezone.utc)
        end_time = start_time + timedelta(days=1)
        ts = TimeStep(timedelta(minutes=1))

        updated = await tv.at(ts, start_time=start_time, stop_time=end_time)
        print(updated[start_time:end_time])

    asyncio.run(access_data())

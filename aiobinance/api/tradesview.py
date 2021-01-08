from __future__ import annotations

from asyncio import Queue, Task
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Callable, Dict, List, Optional

import hypothesis.strategies as st

from aiobinance.api.model.timeinterval import TimeStep
from aiobinance.api.model.trade import Trade
from aiobinance.api.pure.tradesviewbase import TradeFrame, TradesViewBase
from aiobinance.api.rawapi import Binance

# TODO: this should probably done in types instead (metaclass, etc.)
_tradeview_instances: Dict[str, TradesView] = {}

# TODO : request sent to this module (or each possible instance)
# should be done here (globally in module -> unique in sys.modules)
# pbm : it is symbol dependent...


class TradesView(TradesViewBase):
    """ An updateable trades list """

    api: Binance = field(init=True, default=Binance())
    symbol: Optional[str]

    # TODO : aiostream instead of queue here ?
    #  we need to think about combining expectatinos in a way that make sense (Time Interval arithmetic)
    expectations: Optional[Queue]  # containing TimeInterval as the requested dataset

    update_hooks: List[Callable[[TradeFrame], bool]]
    update_loop: Optional[Task]

    @staticmethod
    def strategy(max_size=5):
        return st.builds(
            TradesView,
            api=st.none(),
            symbol=st.text(max_size=5),
            frame=TradeFrame.strategy(max_size=max_size),
        )

    def __new__(cls, api: Binance, symbol: str, frame: TradeFrame = TradeFrame()):

        if symbol in _tradeview_instances.keys():
            return _tradeview_instances[
                symbol
            ]  # to have only one instance for all data.

        self = super(TradesView, cls).__new__(cls)
        # One running loop per symbol, and only one instance !
        _tradeview_instances[symbol] = self
        return self  # init will do the rest

    def __init__(self, api: Binance, symbol: str, frame: TradeFrame = TradeFrame()):
        self.api = api
        self.symbol = symbol

        self.expectations = None  # maybe no async event loop just yet
        self.update_hooks = []  # because multiple things can wait for one update
        self.update_loop = None

        super(TradesView, self).__init__(frame)

    async def request(
        self, start_time: datetime = None, stop_time: datetime = None, **kwargs
    ):
        """ this retrieves recent trades"""

        reqparams = {}

        if start_time is not None:
            # to make sure the timezone is set at this stage (otherwise timestamps will be ambiguous)
            assert start_time.tzinfo is not None
            start_timestamp = int(
                start_time.timestamp() * 1000
            )  # reminder :this should be [ms] precision for binance
            reqparams.update({"startTime": start_timestamp})

        if stop_time is not None:
            assert stop_time.tzinfo is not None
            stop_timestamp = int(
                stop_time.timestamp() * 1000
            )  # reminder :this should be [ms] precision for binance
            reqparams.update({"endTime": stop_timestamp})

        reqparams.update({"symbol": self.symbol})

        reqparams.update({"limit": 1000})

        res = self.api.call_api(command="myTrades", **reqparams)

        if res.is_ok():
            res = res.value
        else:
            raise res.err()  # TODO : a better way ?

        # Binance translation is only a matter of binance json -> python data structure && avoid data duplication.
        # We do not want to change the semantics of the exchange exposed models here.
        trades = [
            Trade(
                time_utc=r["time"] * 1e-3,  # converting [ms] to [s] as float
                symbol=r["symbol"],
                id=r["id"],
                order_id=r["orderId"],
                order_list_id=r["orderListId"],
                price=r["price"],
                qty=r["qty"],
                quote_qty=r["quoteQty"],
                commission=r["commission"],
                commission_asset=r["commissionAsset"],
                is_buyer=r["isBuyer"],
                is_maker=r["isMaker"],
                is_best_match=r["isBestMatch"],
            )
            for r in res
        ]
        # TODO: probably better idea to store data in frame, before converting (but still verifying data type somehow...)
        frame = TradeFrame.from_tradeslist(*trades)
        # We let baseclasse aggregate tradeframes
        return super(TradesView, self).__call__(frame=frame)

    async def loop(self, mini_sleep: timedelta = timedelta(seconds=3)):

        if self.expectations is None:
            self.expectations = Queue()

        # TODO : avoid multiple calls here !!
        if not self.expectations.empty():  # to avoid blocking when not useful
            tint = await self.expectations.get()

            await self.at(  # Note that timeStep is not involved in trade requests
                start_time=tint.start, stop_time=tint.stop
            )

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
        start_time: Optional[datetime] = None,
        stop_time: Optional[datetime] = None,
    ):
        """
        :param start_time: the start_time of data we need to retrieve (might not be returned, use [] to access it if needed)
        :param stop_time: the stop_time of data we need to retrieve (might not be returned, use [] to access it if needed)
        :return:
        """
        if (
            self.frame.empty
            or (start_time is not None and self.frame.time_utc[0] > start_time)
            or (stop_time is not None and self.frame.time_utc[-1] < stop_time)
        ):
            # keep old version
            # Note : for this to work, this must be the only point where it is possible to update the encapsulated data
            old_frame = self.frame

            # do the first request to get recent data, and await
            await self.request(start_time=start_time, stop_time=stop_time)

            # broadcast update
            # TODO : OPTIMIZE THIS ! Difference Computation is too slow...
            frameupdate = self.frame.difference(old_frame)
            # NEW WAY
            if not frameupdate.empty:
                for hook in self.update_hooks:
                    hook(frameupdate)
                    # TODO : somethg useful with return value ? popping the hook ?

        # return the frame
        return self.frame


if __name__ == "__main__":
    import asyncio

    from aiobinance.config import load_api_keyfile

    api = Binance(credentials=load_api_keyfile())
    tv = TradesView(api=api, symbol="COTIBNB")

    async def update():
        # Just because I have data there, put in your own symbol & timeinterval to test
        start_time = datetime.fromtimestamp(1598524340551 / 1000, tz=timezone.utc)
        stop_time = start_time + timedelta(days=1)

        updated = await tv.at(start_time=start_time, stop_time=stop_time)
        print(updated[start_time:stop_time])

    asyncio.run(update())

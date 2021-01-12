from __future__ import annotations

from asyncio import Queue, Task
from dataclasses import field
from datetime import datetime, timedelta, timezone
from typing import Callable, Dict, List, Optional

import hypothesis.strategies as st

from aiobinance.api.model.account_info import AssetAmount
from aiobinance.api.model.asset_info import AssetInfo
from aiobinance.api.model.trade import Trade
from aiobinance.api.model.tradeframe import TradeFrame
from aiobinance.api.pure.ledgerviewbase import LedgerViewBase
from aiobinance.api.rawapi import Binance

# TODO: this should probably done in types instead (metaclass, etc.)
from aiobinance.api.tradesview import TradesView

_ledgerview_instances: Dict[str, LedgerView] = {}

# TODO : request sent to this module (or each possible instance)
# should be done here (globally in module -> unique in sys.modules)
# pbm : it is symbol dependent...


class LedgerView(LedgerViewBase):
    """ An updateable ledger for a coin (gathering multiple tradeframes) """

    trades: dict[str, TradesView]

    api: Binance = field(init=True)

    # TODO : aiostream instead of queue here ?
    #  we need to think about combining expectatinos in a way that make sense (Time Interval arithmetic)
    expectations: Optional[Queue]  # containing TimeInterval as the requested dataset

    # HOOK UP to TRADES updates for now...
    # update_hooks: List[Callable[[TradeFrame], bool]]
    # update_loop: Optional[Task]

    @st.composite
    @staticmethod
    def strategy(draw, max_size=5):
        frames = draw(
            st.lists(elements=TradeFrame.strategy(max_size=max_size), max_size=max_size)
        )
        return LedgerView(
            Binance(),  # just to have something for tests
            draw(st.text(max_size=5)),
            *frames
        )

    def __new__(
        cls, api: Binance, coin: AssetInfo, amount: AssetAmount, *frames: TradeFrame
    ):

        if coin.coin in _ledgerview_instances.keys():
            return _ledgerview_instances[
                coin.coin
            ]  # to have only one instance for all data.

        self = super(LedgerView, cls).__new__(cls)
        # One running loop per symbol, and only one instance !
        _ledgerview_instances[coin.coin] = self
        return self  # init will do the rest

    def __init__(
        self, api: Binance, coin: AssetInfo, amount: AssetAmount, *frames: TradeFrame
    ):
        self.api = api

        self.expectations = None  # maybe no async event loop just yet
        self.update_hooks = []  # because multiple things can wait for one update
        self.update_loop = None

        super(LedgerView, self).__init__(coin, amount, *frames)

    async def request(
        self,
        symbol: str,
        start_time: datetime = None,
        stop_time: datetime = None,
        **kwargs
    ):
        raise NotImplementedError  # binance doesnt have a ledger API, but some exchange do (kraken f.i.)

    async def loop(self, mini_sleep: timedelta = timedelta(seconds=3)):

        if self.expectations is None:
            self.expectations = Queue()

        # TODO : avoid multiple calls here !!
        if not self.expectations.empty():  # to avoid blocking when not useful
            tint = await self.expectations.get()

            for (
                s
            ) in (
                self.trades.keys()
            ):  # TODO: we should probably limit the number of markets to look at ??
                await self.at(  # Note that timeStep is not involved in trade requests
                    symbol=s, start_time=tint.start, stop_time=tint.stop
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
        symbol: str,
        start_time: Optional[datetime] = None,
        stop_time: Optional[datetime] = None,
    ):
        """
        :param start_time: the start_time of data we need to retrieve (might not be returned, use [] to access it if needed)
        :param stop_time: the stop_time of data we need to retrieve (might not be returned, use [] to access it if needed)
        :return:
        """
        if symbol not in self.trades:
            # TODO : verify the symbol indeed has the coin as base or quote asset...
            self.trades[symbol] = TradesView(api=self.api, symbol=symbol)

        if (
            self.trades[symbol].frame.empty
            or (
                start_time is not None
                and self.trades[symbol].frame.time_utc[0] > start_time
            )
            or (
                stop_time is not None
                and self.trades[symbol].frame.time_utc[-1] < stop_time
            )
        ):
            # keep old version
            # Note : for this to work, this must be the only point where it is possible to update the encapsulated data
            # old_frame = self.trades[symbol].frame

            # do the first request to get recent TRADES data, and await
            await self.trades[symbol].at(start_time=start_time, stop_time=stop_time)

            # Let trades manage the update (for now...)

        # return the frame
        return self.trades[symbol].frame


if __name__ == "__main__":
    import asyncio

    from aiobinance.api.account import Account
    from aiobinance.config import load_api_keyfile

    api = Binance(credentials=load_api_keyfile())

    # TODO Is Account really needed here ?? we should probably make it an "optional optimization"...
    acc = Account(api=api)
    asyncio.run(acc())  # retrieve account data

    lv = LedgerView(api=api, coin=acc.assets_info["COTI"], amount=acc.balances["COTI"])

    async def update():
        # Just because I have data there, put in your own symbol & timeinterval to test
        start_time = datetime.fromtimestamp(1598524340551 / 1000, tz=timezone.utc)
        stop_time = start_time + timedelta(days=1)

        updated = await lv.at(
            symbol="COTIBNB", start_time=start_time, stop_time=stop_time
        )
        print(updated[start_time:stop_time])

    asyncio.run(update())

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from functools import cached_property
from typing import Dict, List, Optional

import hypothesis.strategies as st
from hypothesis.strategies import SearchStrategy
from pydantic.dataclasses import dataclass

from aiobinance.api.mock.market import MockMarket
from aiobinance.api.model.exchange_info import ExchangeInfo, RateLimit
from aiobinance.api.model.filters import Filter
from aiobinance.api.pure.exchangebase import ExchangeBase
from aiobinance.api.pure.puremarket import PureMarket
from aiobinance.api.rawapi import Binance


@dataclass(frozen=False)
class MockExchange(ExchangeBase):
    @cached_property
    def markets(self) -> Dict[str, MockMarket]:
        return (
            {s.symbol: MockMarket(info=s) for s in self.info.symbols}
            if self.info is not None
            else {}
        )

    async def __call__(
        self, *, update_delta: Optional[timedelta] = None, **kwargs
    ) -> MockExchange:
        """Mock implementation of an exchange:
        If info is passed, it will update the current value.
        Otherwise, the update delta is used to change the servertime, simulating time progression on the exchange.
        """
        # we simulate time progression, but we dont really wait that long...
        await asyncio.sleep(0.1)

        info = kwargs.get(
            "info", None
        )  # we get the info param as override if present in kwargs

        if info is None:
            try:
                new_servertime = (
                    (self.servertime + update_delta)
                    if update_delta is not None
                    else self.servertime
                )
            except OverflowError:
                # we handle overflow here by preventing any change. we bound the instance in its current state.
                return self

            # otherwise we generate a new ExchangeInfo with properly updated servertime (if it was not passed here)
            info = ExchangeInfo(
                # Note : we take the servertime from the old value, even if it comes from the cache
                servertime=new_servertime,  # time will monotonically increase
                # Here we need to handle the case where info is not present yet...
                # Note this is not the same as having the data with defaults, it only impacts the mock.
                # Having defaults in data formats would impact the actual implementation.
                rate_limits=self.info.rate_limits
                if self.info is not None
                else [],  # this will likely not change
                exchange_filters=self.info.exchange_filters
                if self.info is not None
                else [],  # this will likely not change
                symbols=self.info.symbols
                if self.info is not None
                else [],  # this will likely not change
            )

        # we update the current frozen instance (base class know how to)
        super(MockExchange, self).__call__(info=info)

        return self


if __name__ == "__main__":

    me = MockExchange.strategy().example()
    now = datetime.now(tz=timezone.utc)

    async def run_exchg():
        global now
        print(f"servertime: {me.servertime}")
        print(f"now: {now}")

        newnow = datetime.now(tz=timezone.utc)
        await me(update_delta=newnow - now)
        print(f"servertime: {me.servertime}")
        now = newnow
        print(f"now: {now}")

        await asyncio.sleep(1)

        newnow = datetime.now(tz=timezone.utc)
        await me(update_delta=newnow - now)
        print(f"servertime: {me.servertime}")
        now = newnow
        print(f"now: {now}")

    asyncio.run(run_exchg())

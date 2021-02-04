from __future__ import annotations

import asyncio
import warnings

# CAREFUL : dataclasses from python and pydantic dont mix in hierarchy
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from functools import cached_property
from typing import Dict, Optional, Type

import hypothesis.strategies as st
from result import Err, Ok, Result

from aiobinance.api.mock.mockmarket import MockMarket
from aiobinance.api.model.exchange_info import ExchangeInfo
from aiobinance.api.pure.exchangebase import ExchangeBase


@dataclass(frozen=False)
class MockExchange(ExchangeBase):

    _remote_info: ExchangeInfo = field(
        init=True, default=ExchangeInfo.strategy().example()
    )
    # mandatory to inject test data (representing the remote data)

    @classmethod
    def strategy(
        cls,
        info=st.one_of(st.none(), ExchangeInfo.strategy()),
        _remote_info=ExchangeInfo.strategy(),  # mandatory remote data, used just in case info is None...
        **kwargs,
    ) -> st.SearchStrategy:
        return st.builds(cls, info=info, _remote_info=_remote_info)

    @cached_property
    def markets(self) -> Dict[str, MockMarket]:
        return (
            {s.symbol: MockMarket(info=s) for s in self.info.symbols}
            if self.info is not None
            else {}
        )

    async def __call__(
        self,
        *,
        info: Optional[ExchangeInfo] = None,
        update_delta: Optional[timedelta] = None,
    ) -> ExchangeBase:
        """ This is used to update Exchange's data. it is also here that data can be injected for tests"""

        if info is not None:
            await super(MockExchange, self).__call__(info=info)
            if update_delta:
                warnings.warn(
                    "update_delta ignored because info was provided.\n You should either pass info, or update_delta."
                )
        elif update_delta:
            await super(MockExchange, self).__call__(update_delta=update_delta)

        return self

    async def exchangeinfo(
        self, update_delta: timedelta = timedelta(microseconds=1)
    ) -> Result[ExchangeInfo, OverflowError]:

        try:
            # simulating data update, from existing data if possible, otherwise generate...
            if self.info is None:
                new_info = self._remote_info(update_delta=update_delta)
            else:
                new_info = self.info(update_delta=update_delta)
            return Ok(new_info)

        except OverflowError as oe:
            return Err(oe)


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

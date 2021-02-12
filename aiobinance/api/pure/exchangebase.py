from __future__ import annotations

from dataclasses import (
    dataclass,  # careful to not mix hierarchy of pydantic dataclasses and dataclasses
)
from dataclasses import field
from datetime import MINYEAR, datetime, timedelta, timezone
from functools import cached_property
from typing import Dict, Optional, Type

import hypothesis.strategies as st
from hypothesis.strategies import SearchStrategy
from result import Err, Ok, Result

from aiobinance.api.model.exchange_info import ExchangeInfo
from aiobinance.api.pure.marketbase import MarketBase


@dataclass(frozen=False)
class ExchangeBase:
    info: Optional[ExchangeInfo] = field(init=True, default=None)

    @classmethod
    def strategy(
        cls, info=st.one_of(st.none(), ExchangeInfo.strategy()), **kwargs
    ) -> SearchStrategy:
        return st.builds(cls, info=info)

    @property
    def servertime(self) -> datetime:  # monotonically increase -> start in the past.
        return (
            self.info.servertime
            if self.info is not None
            else datetime(year=MINYEAR, month=1, day=1, tzinfo=timezone.utc)
        )

    @property
    def markets(
        self,
    ) -> Dict[
        str, MarketBase
    ]:  # monotonically increase -> start empty and assume exchange only adds market during a run...
        return (
            {s.symbol: MarketBase(info=s) for s in self.info.symbols}
            if self.info is not None
            else {}
        )

    async def __call__(
        self, *, info: Optional[ExchangeInfo] = None, **kwargs
    ) -> ExchangeBase:
        """ This is used to update Exchange's data. it is also here that data can be injected for tests"""
        if info is None:
            res = await self.exchangeinfo(**kwargs)
            # kwargs are passed to exchangeinfo,
            # in case there is a relevant param

            if res.is_err():
                raise res.err()
            else:
                info = res.ok()

        # we update the current instance
        self.info = info

        return self

    async def exchangeinfo(self, **kwargs) -> Result[ExchangeInfo, NotImplementedError]:
        """ This is a coroutine to be implemented in childrens, with implementation details..."""
        return Err(
            NotImplementedError(
                "This method should be overloaded by a specific implementation."
            )
        )


if __name__ == "__main__":
    import asyncio

    eb = ExchangeBase.strategy().example()
    print(eb)

    eb_updated = asyncio.run(eb(info=ExchangeInfo.strategy().example()))
    print(eb_updated)

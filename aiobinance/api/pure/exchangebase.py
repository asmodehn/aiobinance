from __future__ import annotations

from dataclasses import field
from datetime import MINYEAR, datetime
from typing import Dict, Optional

import hypothesis.strategies as st
from cached_property import cached_property
from hypothesis.strategies import SearchStrategy
from pydantic.dataclasses import dataclass

from aiobinance.api.model.exchange_info import ExchangeInfo
from aiobinance.api.pure.puremarket import PureMarket


@dataclass(frozen=False)
class ExchangeBase:
    info: Optional[ExchangeInfo] = field(init=True, default=None)

    @classmethod
    def strategy(
        cls, info=st.one_of(st.none(), ExchangeInfo.strategy()), **kwargs
    ) -> SearchStrategy:
        return st.builds(cls, info=info)

    @cached_property
    def servertime(self) -> datetime:  # monotonically increase -> start in the past.
        return (
            self.info.servertime
            if self.info is not None
            else datetime(year=MINYEAR, month=1, day=1)
        )

    @cached_property
    def markets(
        self,
    ) -> Dict[
        str, PureMarket
    ]:  # monotonically increase -> start empty and assume exchange only adds market during a run...
        return (
            {s.symbol: PureMarket(info=s) for s in self.info.symbols}
            if self.info is not None
            else {}
        )

    def __call__(
        self, *, info: Optional[ExchangeInfo] = None, **kwargs
    ) -> ExchangeBase:
        # return same instance if no change
        if info is None:
            return self

        popping = []
        if self.info is None:
            # because we may have cached invalid values from initialization (self.info was None)
            popping.append("markets")
            popping.append("servertime")
        else:  # otherwise we detect change with equality on frozen dataclass fields
            if self.info.servertime != info.servertime:
                popping.append("servertime")
            if self.info.symbols != info.symbols:
                popping.append("markets")

        # updating by updating data
        self.info = info

        # and invalidating related caches
        for p in popping:
            self.__dict__.pop(p, None)

        # returning self to allow chaining
        return self


if __name__ == "__main__":
    ei = ExchangeBase.strategy().example()
    print(ei)
    ei_updated = ei(info_update=ExchangeInfo.strategy().example())
    print(ei_updated)

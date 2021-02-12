from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from functools import cached_property
from typing import Dict, List, Optional, Tuple

import hypothesis.strategies as st
from hypothesis.strategies import SearchStrategy
from result import Err, Ok, Result

from aiobinance.api.model.account_info import AssetAmount
from aiobinance.api.model.asset_info import AssetInfo
from aiobinance.api.model.filters import Filter
from aiobinance.api.model.market_info import MarketInfo
from aiobinance.api.model.order import LimitOrder, MarketOrder, OrderSide
from aiobinance.api.model.tradeframe import TradeFrame
from aiobinance.api.pure.ledgerviewbase import LedgerViewBase
from aiobinance.api.pure.marketbase import MarketBase
from aiobinance.api.pure.ohlcviewbase import OHLCFrame, OHLCViewBase
from aiobinance.api.pure.tradesviewbase import TradesViewBase


@dataclass(frozen=False)
class AssetBase:
    # Note: not all assets have info apparently...
    info: Optional[AssetInfo] = field(init=True, default=None)

    # This can change, but it must pass via __call__
    amount: Optional[AssetAmount] = field(init=True, default=None)

    # These are assumed static and immutable
    base_markets: List[MarketBase] = field(init=True, default_factory=list)
    quote_markets: List[MarketBase] = field(init=True, default_factory=list)

    @classmethod
    def strategy(cls) -> SearchStrategy:
        return st.builds(cls, info=AssetInfo.strategy())

    @cached_property
    def ledger(self) -> LedgerViewBase:
        if self.info is None:
            raise NotImplementedError
        else:
            return LedgerViewBase(
                coin=self.info,
                base_trades={m.info.symbol: m.trades for m in self.base_markets},
                quote_trades={m.info.symbol: m.trades for m in self.quote_markets},
            )

    async def __call__(
        self,
        *,
        info: Optional[AssetInfo] = None,
        amount: Optional[AssetAmount] = None,
        **kwargs
    ) -> AssetBase:
        """ This is used to update Market's data. it is also here that data can be injected for tests"""
        if info is None:
            res = await self.assetinfo(**kwargs)
            # kwargs are passed to marketinfo,
            # in case there is a relevant param

            if res.is_err():
                raise res.err()
            else:
                info = res.ok()

        if amount is None:
            res = await self.amountrequest(**kwargs)

            if res.is_err():
                raise res.err()
            else:
                amount = res.ok()

        # we update the current instance
        self.info = info
        self.amount = amount

        return self

    async def assetinfo(self, **kwargs) -> Result[AssetInfo, NotImplementedError]:
        """ This is a coroutine to be implemented in childrens, with implementation details..."""
        return Err(
            NotImplementedError(
                "This method should be overloaded by a specific implementation."
            )
        )

    async def amountrequest(self, **kwargs) -> Result[AssetAmount, NotImplementedError]:
        return Err(
            NotImplementedError(
                "This method should be overloaded by a specific implementation."
            )
        )


if __name__ == "__main__":
    import asyncio

    ab = AssetBase.strategy().example()
    print(ab)

    ab_updated = asyncio.run(
        ab(info=AssetInfo.strategy().example(), amount=AssetAmount.strategy().example())
    )
    print(ab_updated)

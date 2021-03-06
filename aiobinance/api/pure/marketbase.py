from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from functools import cached_property
from typing import Dict, List, Optional, Tuple

import hypothesis.strategies as st
from hypothesis.strategies import SearchStrategy
from result import Err, Ok, Result

from aiobinance.api.model.filters import Filter
from aiobinance.api.model.market_info import MarketInfo
from aiobinance.api.model.order import LimitOrder, MarketOrder, OrderSide
from aiobinance.api.model.tradeframe import TradeFrame
from aiobinance.api.pure.ohlcviewbase import OHLCFrame, OHLCViewBase
from aiobinance.api.pure.tradesviewbase import TradesViewBase


@dataclass(frozen=False)
class MarketBase:
    info: Optional[MarketInfo] = field(init=True, default=None)

    @classmethod
    def strategy(cls) -> SearchStrategy:
        return st.builds(cls, info=MarketInfo.strategy())

    @cached_property
    def price(self) -> OHLCViewBase:
        if self.info is None:
            return (
                OHLCViewBase()
            )  # there should be a special case also in child classes
        else:
            return OHLCViewBase()

    @cached_property
    def trades(self) -> TradesViewBase:
        # Note : A "random local mock matching engine" should be implemented as same level as market
        # As randomness is a side effect... Call it 'FakeMarket' maybe, it could return a "balanced set of trades",
        # that is something plausible, useful for tests, yet without longterm side-effects (given our simple box-based algorithms)
        # BUT NOT HERE ! lets try to remain side-effect-free here...
        if self.info is None:
            return TradesViewBase(
                symbol=None
            )  # there should be a special case also in child classes
        else:
            return TradesViewBase(symbol=self.info.symbol)

    async def __call__(
        self, *, info: Optional[MarketInfo] = None, **kwargs
    ) -> MarketBase:
        """ This is used to update Market's data. it is also here that data can be injected for tests"""
        if info is None:
            res = await self.marketinfo(**kwargs)
            # kwargs are passed to marketinfo,
            # in case there is a relevant param

            if res.is_err():
                raise res.err()
            else:
                info = res.ok()

        # we update the current instance
        self.info = info

        return self

    async def marketinfo(self, **kwargs) -> Result[MarketInfo, NotImplementedError]:
        """ This is a coroutine to be implemented in childrens, with implementation details..."""
        return Err(
            NotImplementedError(
                "This method should be overloaded by a specific implementation."
            )
        )

    # TODO : async
    def limit_order(
        self,
        *,
        side: OrderSide,
        price: Decimal,
        quantity: Decimal,
        timeInForce="GTC",
        icebergQty: Optional[Decimal] = None,
        # Note : return type must be same as implementation
        # (even if there will be no exception here)
    ) -> Result[LimitOrder, Exception]:

        """ A limit order passing without any side effect. """

        sent_params = self.info._limit_order_params(
            side=side,
            price=price,
            quantity=quantity,
            timeInForce=timeInForce,
            icebergQty=icebergQty,
        )

        # filling up with order info, as it has been accepted
        return Ok(
            LimitOrder(
                symbol=sent_params["symbol"],
                side=OrderSide(sent_params["side"]),
                type=sent_params["type"],
                timeInForce=sent_params["timeInForce"],
                # we recreate decimal from passed string to adjust precision...
                origQty=Decimal(sent_params["quantity"]),
                price=Decimal(sent_params["price"]),
                # fake attr for test order
                order_id=-1,
                order_list_id=-1,
                clientOrderId="",
                transactTime=int(datetime.now(tz=timezone.utc).timestamp() * 1000),
                executedQty=Decimal(0),
                cummulativeQuoteQty=Decimal(0),
                status="TEST",
                fills=[],
            )
        )


if __name__ == "__main__":
    import asyncio

    mb = MarketBase.strategy().example()
    print(mb)

    mb_updated = asyncio.run(mb(info=MarketInfo.strategy().example()))
    print(mb_updated)

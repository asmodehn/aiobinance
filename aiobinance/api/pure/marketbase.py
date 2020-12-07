from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

import hypothesis.strategies as st
from cached_property import cached_property
from hypothesis.strategies import SearchStrategy
from result import Ok, Result

from aiobinance.api.model.filters import Filter
from aiobinance.api.model.market_info import MarketInfo
from aiobinance.api.model.order import LimitOrder, MarketOrder, OrderSide
from aiobinance.api.pure.ohlcviewbase import OHLCFrame, OHLCViewBase
from aiobinance.api.pure.tradesviewbase import TradesViewBase
from aiobinance.model import TradeFrame


@dataclass(frozen=False)
class MarketBase:  # TODO : rename to MakertBase for clarity...
    info: Optional[MarketInfo] = field(init=True, default=None)

    @classmethod
    def strategy(cls) -> SearchStrategy:
        return st.builds(cls, info=MarketInfo.strategy())

    @cached_property
    def price(self) -> OHLCViewBase:
        # TODO : actual API request
        return OHLCViewBase()

    @cached_property
    def trades(  # TODO : build a pure mock version we can use for simulations...
        self,
    ) -> TradesViewBase:
        # Note : A "random local mock matching engine" should be implemented as same level as market
        # As randomness is a side effect... Call it 'FakeMarket' maybe, it could return a "balanced set of trades",
        # that is something plausible, useful for tests, yet without longterm side-effects (given our simple box-based algorithms)
        # BUT NOT HERE ! lets try to remain side-effect-free here...

        return TradesViewBase()

    def __call__(self, *, info: Optional[MarketInfo] = None, **kwargs) -> MarketBase:
        # return same instance if no change
        if info is None:
            return self

        popping = []
        if self.info is None:
            # because we may have cached invalid values from initialization (self.info was None)
            popping.append("trades")
        else:  # otherwise we detect change with equality on frozen dataclass fields
            if self.info.symbol != info.symbol:
                popping.append("trades")  # because trades depend on symbol

        # updating by updating data
        self.info = info

        # and invalidating related caches
        for p in popping:
            self.__dict__.pop(p, None)

        # returning self to allow chaining
        return self

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
    mb = MarketBase.strategy().example()
    print(mb)
    mb_updated = mb(info=MarketInfo.strategy().example())
    print(mb_updated)

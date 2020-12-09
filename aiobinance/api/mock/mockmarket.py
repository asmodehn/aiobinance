from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

import hypothesis.strategies as st
from cached_property import cached_property
from hypothesis.strategies import SearchStrategy
from result import Ok, Result

from aiobinance.api.model.market_info import MarketInfo
from aiobinance.api.model.order import LimitOrder, OrderSide
from aiobinance.api.model.tradeframe import TradeFrame
from aiobinance.api.pure.marketbase import MarketBase
from aiobinance.api.pure.tradesviewbase import TradesViewBase


@dataclass(frozen=False)
class MockMarket(MarketBase):
    @cached_property
    def trades(self) -> TradesViewBase:  # using base while wai
        return (
            TradesViewBase()  # pass symbol ???
            if self.info is not None
            else TradesViewBase()
        )

    async def __call__(
        self, *, update_delta: Optional[timedelta] = None, **kwargs
    ) -> MockMarket:
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

            # otherwise we generate a new MarketInfo with properly updated values (if it was not passed here)
            info = MarketInfo.strategy().example()  # TODO : something meaningful

        # we update the current frozen instance (base class know how to)
        super(MockMarket, self).__call__(info=info)

        return self

    def matching_update(self):
        # TODO : some kind of matching engine, to transform passed order into trades...
        pass

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

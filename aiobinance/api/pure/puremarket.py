from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

import hypothesis.strategies as st
from hypothesis.strategies import SearchStrategy
from pydantic.dataclasses import dataclass
from result import Ok, Result

from aiobinance.api.model.filters import Filter
from aiobinance.api.model.market_info import MarketInfo
from aiobinance.api.model.order import LimitOrder, MarketOrder, OrderSide


@dataclass
class PureMarket:
    info: MarketInfo

    @classmethod
    def strategy(cls) -> SearchStrategy:
        return st.builds(cls, info=MarketInfo.strategy())

    def __init__(self, info: MarketInfo):
        self.info = info

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

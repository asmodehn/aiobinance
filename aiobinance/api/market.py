from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional

from cached_property import cached_property
from result import Err, Ok, Result

from aiobinance.api.model.market_info import MarketInfo
from aiobinance.api.model.order import LimitOrder, MarketOrder, OrderFill, OrderSide
from aiobinance.api.model.pricecandle import PriceCandle
from aiobinance.api.model.trade import Trade
from aiobinance.api.ohlcview import OHLCView
from aiobinance.api.pure.marketbase import MarketBase
from aiobinance.api.pure.ticker import Ticker
from aiobinance.api.rawapi import Binance
from aiobinance.api.tradesview import TradesView


@dataclass(frozen=False)
class Market(MarketBase):
    """A class to simplify interacting with binance markets through the REST API.
    Here we inherit from PureMarket, to get same methods signatures, therefore specifying the same behavior,
     as with PureMarket which we test thoroughly without side effect.
    While leveraging the inheritance relationship as a way to specify behavior of effectful code...
    """

    api: Binance = field(init=True, default=Binance())
    test: bool = field(init=True, default=True)

    async def __call__(self, *args, **kwargs):
        """ triggers an update (polling style)"""
        raise NotImplementedError  # This is an optimization on simple request -> later

    @cached_property
    def price(self) -> OHLCView:
        if self.info is None:
            return OHLCView(api=self.api)
        else:
            return OHLCView(api=self.api, symbol=self.info.symbol)

    @cached_property
    def trades(self) -> TradesView:
        if self.info is None:
            return TradesView(api=self.api)
        else:
            return TradesView(api=self.api, market=self.info.symbol)

    def ticker24(
        self,
    ) -> Ticker:  # TODO : build a pure mock version we can use for simulations...
        res = self.api.call_api(
            command="ticker24hr",
            symbol=self.info.symbol,
        )

        if res.is_ok():
            res = res.value
        else:
            # TODO : handle API error properly
            raise RuntimeError(res.value)

        # Binance translation is only a matter of binance json -> python data structure && avoid data duplication.
        # We do not want to change the semantics of the exchange exposed models here.
        return Ticker(
            symbol=res["symbol"],
            price_change=res["priceChange"],
            price_change_percent=res["priceChangePercent"],
            weighted_avg_price=res["weightedAvgPrice"],
            prev_close_price=res["prevClosePrice"],
            last_price=res["lastPrice"],
            last_qty=res["lastQty"],
            bid_price=res["bidPrice"],
            ask_price=res["askPrice"],
            open_price=res["openPrice"],
            high_price=res["highPrice"],
            low_price=res["lowPrice"],
            volume=res["volume"],
            quote_volume=res["quoteVolume"],
            open_time=res["openTime"],
            close_time=res["closeTime"],
            first_id=res["firstId"],
            last_id=res["lastId"],
            count=res["count"],
        )

    # TODO :
    #  newOrderRespType: Optional[str] =None     # Set the response JSON. ACK, RESULT, or FULL; MARKET and LIMIT order types default to FULL, all other orders default to ACK.
    #  recvWindow: Optional[int] =None          # The value cannot be greater than 60000

    def limit_order(
        self,
        *,
        side: OrderSide,
        price: Decimal,
        quantity: Decimal,
        timeInForce="GTC",
        icebergQty: Optional[Decimal] = None,
    ) -> Result[LimitOrder, Exception]:

        sent_params = self.info._limit_order_params(
            side=side,
            quantity=quantity,
            price=price,
            timeInForce=timeInForce,
            icebergQty=icebergQty,
        )

        if self.test:
            res = self.api.call_api(command="testOrder", **sent_params)
        else:
            res = self.api.call_api(command="createOrder", **sent_params)

        if res.is_ok():
            res = res.value
            if self.test:
                test_order = super(Market, self).limit_order(
                    side=side,
                    quantity=quantity,
                    price=price,
                    timeInForce=timeInForce,
                    icebergQty=icebergQty,
                )

                return test_order
            else:
                return Ok(
                    LimitOrder(
                        symbol=res["symbol"],
                        order_id=res["orderId"],
                        order_list_id=res["orderListId"],
                        clientOrderId=res["clientOrderId"],
                        transactTime=res["transactTime"],
                        price=res["price"],
                        origQty=res["origQty"],
                        executedQty=res["executedQty"],
                        cummulativeQuoteQty=res["cummulativeQuoteQty"],
                        status=res["status"],
                        timeInForce=res["timeInForce"],
                        type=res["type"],
                        side=res["side"],
                        fills=[OrderFill(**f) for f in res["fills"]],
                    )
                )

        else:
            # TODO : handle API error properly
            raise RuntimeError(res.value)


if __name__ == "__main__":
    raise NotImplementedError
    # TODO : some interactive repl to test it manually...

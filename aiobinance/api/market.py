from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional

from result import Err, Ok, Result

from aiobinance.api.model.market_info import MarketInfo
from aiobinance.api.model.order import LimitOrder, MarketOrder, OrderFill, OrderSide
from aiobinance.api.pure.puremarket import PureMarket
from aiobinance.api.pure.ticker import Ticker
from aiobinance.api.rawapi import Binance
from aiobinance.model import OHLCV, TradeFrame
from aiobinance.model.ohlcv import Candle
from aiobinance.model.trade import Trade


class Market(PureMarket):
    """A class to simplify interacting with binance markets through the REST API.
    Here we inherit from PureMarket, to get same methods signatures, therefore specifying the same behavior,
     as with PureMarket which we test thoroughly without side effect.
    While leveraging the inheritance relationship as a way to specify behavior of effectful code...
    """

    api: Binance

    def __init__(
        self,
        api: Binance,
        info: MarketInfo,
        async_loop=None,
    ):

        # if an async loop is passed, call is run in the background to update data out-of-band
        # currently polling in the background, later TODO : websockets

        self.api = api
        super(Market, self).__init__(info=info)

    def __call__(self, *args, **kwargs):
        """ triggers an update (polling style)"""
        raise NotImplementedError  # This is an optimization on simple request -> later

    def price(  # TODO : build a pure mock version we can use for simulations...
        self, *, start_time: datetime, end_time: datetime, interval=None
    ) -> OHLCV:

        # to make sure the timezone is set at this stage (otherwise timestamps will be ambiguous)
        assert start_time.tzinfo is not None
        assert end_time.tzinfo is not None

        start_timestamp = int(start_time.timestamp() * 1000)
        end_timestamp = int(end_time.timestamp() * 1000)
        interval = (
            interval
            if interval is not None
            else self.api.interval(start_timestamp, end_timestamp)
        )

        res = self.api.call_api(
            command="klines",
            symbol=self.info.symbol,
            interval=interval,
            startTime=start_timestamp,
            endTime=end_timestamp,
            limit=1000,
        )

        if res.is_ok():
            res = res.value

        # Binance translation is only a matter of binance json -> python data structure && avoid data duplication.
        # We do not want to change the semantics of the exchange exposed models here.
        candles = [
            Candle(
                open_time=r[0],
                open=r[1],
                high=r[2],
                low=r[3],
                close=r[4],
                volume=r[5],
                close_time=r[6],
                qav=r[7],
                num_trades=r[8],
                taker_base_vol=r[9],
                taker_quote_vol=r[10],
                is_best_match=r[11],
            )
            for r in res
        ]

        return OHLCV(*candles)

    def trades(  # TODO : build a pure mock version we can use for simulations...
        self,
        *,
        start_time: datetime,
        end_time: datetime,
    ) -> TradeFrame:

        # to make sure the timezone is set at this stage (otherwise timestamps will be ambiguous)
        assert start_time.tzinfo is not None
        assert end_time.tzinfo is not None

        start_timestamp = int(start_time.timestamp() * 1000)
        end_timestamp = int(end_time.timestamp() * 1000)

        res = self.api.call_api(
            command="myTrades",
            symbol=self.info.symbol,
            startTime=start_timestamp,
            endTime=end_timestamp,
            limit=1000,
        )

        if res.is_ok():
            res = res.value

        # Binance translation is only a matter of binance json -> python data structure && avoid data duplication.
        # We do not want to change the semantics of the exchange exposed models here.
        trades = [
            Trade(
                time=r["time"],
                symbol=r["symbol"],
                id=r["id"],
                order_id=r["orderId"],
                order_list_id=r["orderListId"],
                price=r["price"],
                qty=r["qty"],
                quote_qty=r["quoteQty"],
                commission=r["commission"],
                commission_asset=r["commissionAsset"],
                is_buyer=r["isBuyer"],
                is_maker=r["isMaker"],
                is_best_match=r["isBestMatch"],
            )
            for r in res
        ]

        # We aggregate all formatted trades into a TradeFrame
        return TradeFrame(*trades)

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

    def market_order(
        self,
        *,
        side: OrderSide,
        quantity: Optional[Decimal] = None,
        quote_order_qty: Optional[Decimal] = None,
        test=True,  # test order by default for safety
    ) -> Result[MarketOrder, None]:

        # quick assert check
        # TODO : decide if we have two methods, or none at all...
        if quantity is not None:
            assert (
                quote_order_qty is None
            ), "Both quantity and quoteOrderQty params cannot be set for send_market_buy_order()"
        elif quote_order_qty is not None:
            assert (
                quantity is None
            ), "Both quantity and quoteOrderQty params cannot be set for send_market_buy_order()"

        if quote_order_qty is not None:
            # not implemented just yet...
            sent_params = self.info._market_order_quote_params(
                side=side, quantity=quote_order_qty
            )

            test_order = super(Market, self).market_order_quote(
                side=side, quantity=quote_order_qty
            )
        else:
            sent_params = self.info._market_order_base_params(
                side=side, quantity=quantity
            )
            test_order = super(Market, self).market_order_base(
                side=side, quantity=quantity
            )

        if test:
            res = self.api.call_api(command="testOrder", **sent_params)

            if res.is_ok():
                res = res.value
            else:
                # TODO : handle API error properly
                raise RuntimeError(res.value)

            return Ok(test_order)

        else:
            res = self.api.call_api(command="createOrder", **sent_params)

            if res.is_ok():
                res = res.value
            else:
                # TODO : handle API error properly
                raise RuntimeError(res.value)

            return Ok(
                MarketOrder(
                    symbol=res["symbol"],
                    order_id=res["orderId"],
                    order_list_id=res["orderListId"],
                    clientOrderId=res["clientOrderId"],
                    transactTime=res["transactTime"],
                    # price=res['price'],  # price is set but at '0.0' and doesnt hold any meaning...
                    origQty=res["origQty"],
                    executedQty=res["executedQty"],
                    cummulativeQuoteQty=res["cummulativeQuoteQty"],
                    status=res["status"],
                    # timeInForce=res['timeInForce'],# seems this is always GTC, and doesnt hold much value with market orders that are execute ASAP...
                    type=res["type"],
                    side=res["side"],
                    fills=[OrderFill(**f) for f in res["fills"]],
                )
            )

    def limit_order(
        self,
        *,
        side: OrderSide,
        price: Decimal,
        quantity: Decimal,
        timeInForce="GTC",
        icebergQty: Optional[Decimal] = None,
        test=True,  # test order by default for safety
    ) -> Result[LimitOrder, None]:

        sent_params = self.info._limit_order_params(
            side=side, quantity=quantity, price=price
        )

        if icebergQty is not None:
            sent_params.update(
                {
                    "icebergQty": icebergQty,
                }
            )

        if test:
            res = self.api.call_api(command="testOrder", **sent_params)

            if res.is_ok():
                res = res.value
            else:
                # TODO : handle API error properly
                raise RuntimeError(res.value)

            test_order = super(Market, self).limit_order(
                side=side, quantity=quantity, price=price
            )

            # TODO : review if sequence here...
            if res == {}:
                # filling up with order info, as it has been accepted
                return Ok(test_order)
        else:
            res = self.api.call_api(command="createOrder", **sent_params)

            if res.is_ok():
                res = res.value
            else:
                # TODO : handle API error properly
                raise RuntimeError(res.value)

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


if __name__ == "__main__":
    raise NotImplementedError
    # TODO : some interactive repl to test it manually...

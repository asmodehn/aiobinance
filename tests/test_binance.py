from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from result import Result

import aiobinance.binance
from aiobinance.api.model.order import LimitOrder, MarketOrder, OrderFill, OrderSide
from aiobinance.api.pure.ticker import Ticker


@pytest.mark.vcr
def test_ticker_from_binance():
    """ get binance ticker"""
    ticker = aiobinance.binance.ticker24_from_binance("COTIBNB")

    assert isinstance(ticker, Ticker)

    assert ticker.ask_price == Decimal("0.00120300")
    assert ticker.bid_price == Decimal("0.00119900")
    assert ticker.close_time == datetime(
        year=2020,
        month=11,
        day=9,
        hour=17,
        minute=17,
        microsecond=79000,
        tzinfo=timezone.utc,
    )
    assert ticker.count == 2810
    assert ticker.first_id == 454001
    assert ticker.high_price == Decimal("0.00126300")
    assert ticker.last_id == 456810
    assert ticker.last_price == Decimal("0.00120200")
    assert ticker.last_qty == Decimal("3004.00000000")
    assert ticker.low_price == Decimal("0.00114700")
    assert ticker.open_price == Decimal("0.00126200")
    assert ticker.open_time == datetime(
        year=2020,
        month=11,
        day=8,
        hour=17,
        minute=17,
        microsecond=79000,
        tzinfo=timezone.utc,
    )
    assert ticker.prev_close_price == Decimal("0.00125800")
    assert ticker.price_change == Decimal("-0.000060000")
    assert ticker.price_change_percent == Decimal("-4.754")
    assert ticker.quote_volume == Decimal("3631.82546700")
    assert ticker.symbol == "COTIBNB"
    assert ticker.volume == Decimal("3013981.00000000")
    assert ticker.weighted_avg_price == Decimal("0.00120499")


@pytest.mark.vcr(
    filter_headers=["X-MBX-APIKEY"], filter_query_parameters=["timestamp", "signature"]
)
def test_limitorder_test_to_binance(keyfile):
    """ send orders to binance """

    res_order = aiobinance.binance.limitorder_to_binance(
        symbol="COTIBNB",
        side=OrderSide("BUY"),
        quantity=Decimal("300"),
        price=Decimal("0.0015"),
        credentials=keyfile,
    )

    assert res_order and isinstance(res_order, Result)
    assert isinstance(res_order.value, LimitOrder)
    assert res_order.value.clientOrderId == ""
    assert res_order.value.cummulativeQuoteQty.is_zero()
    assert res_order.value.executedQty.is_zero()
    assert res_order.value.fills == []
    assert res_order.value.icebergQty is None
    assert res_order.value.order_id == -1
    assert res_order.value.order_list_id == -1
    assert res_order.value.origQty == Decimal("300")
    assert res_order.value.price == Decimal("0.0015")
    assert res_order.value.side == OrderSide.BUY
    assert res_order.value.status == "TEST"
    assert res_order.value.symbol == "COTIBNB"
    assert res_order.value.timeInForce == "GTC"
    assert res_order.value.type == "LIMIT"

    # transac time has a dynamic value because it does not depend on recorded traffic !
    # This is measuring with second precision a time in ms
    assert res_order.value.transactTime // 1000 == int(
        datetime.now(tz=timezone.utc).timestamp()
    )


@pytest.mark.vcr(
    filter_headers=["X-MBX-APIKEY"], filter_query_parameters=["timestamp", "signature"]
)
def test_limitorder_to_binance(keyfile):
    """ send orders to binance """

    res_order = aiobinance.binance.limitorder_to_binance(
        symbol="COTIBNB",
        side=OrderSide("BUY"),
        quantity=Decimal("300"),
        price=Decimal("0.0015"),
        credentials=keyfile,
        test=False,
    )

    assert res_order and isinstance(res_order, Result)
    assert isinstance(res_order.value, LimitOrder)
    assert res_order.value.clientOrderId == "UIwsOoNnCNJlxHFCwtikDI"
    assert res_order.value.cummulativeQuoteQty.is_zero()
    assert res_order.value.executedQty.is_zero()
    assert res_order.value.fills == []
    assert res_order.value.icebergQty is None
    assert res_order.value.order_id == 31085682
    assert res_order.value.order_list_id == -1
    assert res_order.value.origQty == Decimal("300")
    assert res_order.value.price == Decimal("0.0015")
    assert res_order.value.side == OrderSide.BUY
    assert res_order.value.status == "NEW"
    assert res_order.value.symbol == "COTIBNB"
    assert res_order.value.timeInForce == "GTC"
    assert res_order.value.transactTime == 1605967825942
    assert res_order.value.type == "LIMIT"


if __name__ == "__main__":
    pytest.main(["-s", __file__, "--block-network"])
    # record run
    # pytest.main(['-s', __file__, '--with-keyfile', '--record-mode=new_episodes'])

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from aiobinance.api.account import Account
from aiobinance.api.exchange import Exchange
from aiobinance.api.model.order import LimitOrder, OrderSide
from aiobinance.api.rawapi import Binance
from aiobinance.trader import Trader


@pytest.mark.asyncio
@pytest.mark.vcr(
    filter_headers=["X-MBX-APIKEY"], filter_query_parameters=["timestamp", "signature"]
)
async def test_buy_test(keyfile):
    """ have the trader buy something """

    api = Binance(credentials=keyfile)  # we might need private requests here !

    account = Account(api=api, test=True)

    # await account()
    await account.exchange()  # updating exchange to access markets

    trader = Trader(account=account, market=account.exchange.markets["COTIBNB"])

    # Buy test order overpriced => will readjust !
    # Decimal of float here to test precision. it should be built from string instead !
    order = await trader.buy(amount=Decimal(300), total_expected=Decimal(0.45))
    assert isinstance(order, LimitOrder), f"{order}"
    assert order.clientOrderId == ""
    assert order.cummulativeQuoteQty.is_zero()
    assert order.executedQty.is_zero()
    assert order.fills == []
    assert order.icebergQty is None
    assert order.order_id == -1
    assert order.order_list_id == -1
    assert order.origQty == Decimal("300")
    assert order.price == Decimal(
        "0.00142200"
    )  # calculated price from expectation & readjusted, at correct precision.
    assert order.side == OrderSide.BUY
    assert order.status == "TEST"
    assert order.symbol == "COTIBNB"
    assert order.timeInForce == "GTC"

    # transac time has a dynamic value because it does not depend on recorded traffic !
    # This is measuring with second precision a time in ms
    assert order.transactTime // 1000 == int(datetime.now(tz=timezone.utc).timestamp())

    # Buy test order underpriced
    # Note: it seems that PRICE_FILTER can prevent passing buy orders too far from current price...
    # Decimal of float here to test precision. it should be built from string instead !
    order = await trader.buy(amount=Decimal(300), total_expected=Decimal(0.42))
    assert isinstance(order, LimitOrder), f"{order}"
    assert order.clientOrderId == ""
    assert order.cummulativeQuoteQty.is_zero()
    assert order.executedQty.is_zero()
    assert order.fills == []
    assert order.icebergQty is None
    assert order.order_id == -1
    assert order.order_list_id == -1
    assert order.origQty == Decimal("300")
    assert order.price == Decimal(
        "0.00140000"
    )  # calculated price from expectation, with correct precision.
    assert order.side == OrderSide.BUY
    assert order.status == "TEST"
    assert order.symbol == "COTIBNB"
    assert order.timeInForce == "GTC"

    # transac time has a dynamic value because it does not depend on recorded traffic !
    # This is measuring with second precision a time in ms
    assert order.transactTime // 1000 == int(datetime.now(tz=timezone.utc).timestamp())


@pytest.mark.skip  # skip this while market is not in our interest... recording TODO
@pytest.mark.asyncio
@pytest.mark.vcr(
    filter_headers=["X-MBX-APIKEY"], filter_query_parameters=["timestamp", "signature"]
)
async def test_buy(keyfile):
    """ have the trader buy something """

    api = Binance(credentials=keyfile)  # we might need private requests here !

    exchange = Exchange(api=api, test=False)

    await exchange()

    trader = Trader(account=exchange.account, market=exchange.markets["COTIBNB"])

    print("Buy test order: ")
    # Decimal of float here to test precision. it should be built from string instead !
    order = await trader.buy(amount=Decimal(300), total_expected=Decimal(0.45))
    print(order)

    assert order


@pytest.mark.asyncio
@pytest.mark.vcr(
    filter_headers=["X-MBX-APIKEY"], filter_query_parameters=["timestamp", "signature"]
)
async def test_sell_test(keyfile):
    """ have the trader buy something """

    api = Binance(credentials=keyfile)  # we might need private requests here !

    account = Account(api=api, test=True)

    await account.exchange()

    trader = Trader(account=account, market=account.exchange.markets["COTIBNB"])

    # Sell test order overpriced
    # Decimal of float here to test precision. it should be built from string instead !
    order = await trader.sell(amount=Decimal(300), total_expected=Decimal(0.45))
    assert order and isinstance(order, LimitOrder)
    assert order.clientOrderId == ""
    assert order.cummulativeQuoteQty.is_zero()
    assert order.executedQty.is_zero()
    assert order.fills == []
    assert order.icebergQty is None
    assert order.order_id == -1
    assert order.order_list_id == -1
    assert order.origQty == Decimal("300")
    assert order.price == Decimal(
        "0.00150000"
    )  # calculated price from expectation, with correct precision.
    assert order.side == OrderSide.SELL
    assert order.status == "TEST"
    assert order.symbol == "COTIBNB"
    assert order.timeInForce == "GTC"

    # transac time has a dynamic value because it does not depend on recorded traffic !
    # This is measuring with second precision a time in ms
    assert order.transactTime // 1000 == int(datetime.now(tz=timezone.utc).timestamp())

    # Sell test order underpriced => will readjust !
    # Decimal of float here to test precision. it should be built from string instead !
    order = await trader.sell(amount=Decimal(300), total_expected=Decimal(0.40))
    assert order and isinstance(order, LimitOrder)
    assert order.clientOrderId == ""
    assert order.cummulativeQuoteQty.is_zero()
    assert order.executedQty.is_zero()
    assert order.fills == []
    assert order.icebergQty is None
    assert order.order_id == -1
    assert order.order_list_id == -1
    assert order.origQty == Decimal("300")
    assert order.price == Decimal(
        "0.00142300"
    )  # calculated price from expectation & adjusted, with correct precision.
    assert order.side == OrderSide.SELL
    assert order.status == "TEST"
    assert order.symbol == "COTIBNB"
    assert order.timeInForce == "GTC"

    # transac time has a dynamic value because it does not depend on recorded traffic !
    # This is measuring with second precision a time in ms
    assert order.transactTime // 1000 == int(datetime.now(tz=timezone.utc).timestamp())


@pytest.mark.skip  # skip this while market is not in our interest... recording TODO
@pytest.mark.asyncio
@pytest.mark.vcr(
    filter_headers=["X-MBX-APIKEY"], filter_query_parameters=["timestamp", "signature"]
)
async def test_sell(keyfile):
    """ have the trader buy something """

    api = Binance(credentials=keyfile)  # we might need private requests here !

    exchange = Exchange(api=api, test=False)

    await exchange()

    trader = Trader(account=exchange.account, market=exchange.markets["COTIBNB"])

    print("Sell test order: ")
    # Decimal of float here to test precision. it should be built from string instead !
    order = await trader.sell(amount=Decimal(300), total_expected=Decimal(0.45))
    print(order)

    assert order


if __name__ == "__main__":
    pytest.main(["-s", __file__, "--block-network"])
    # record run
    # pytest.main(['-s', __file__, '--with-keyfile', '--record-mode=new_episodes'])

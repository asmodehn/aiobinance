from datetime import datetime, timezone
from decimal import Decimal

import pytest

from aiobinance.api.account import retrieve_account
from aiobinance.api.rawapi import Binance
from aiobinance.config import Credentials, load_api_keyfile
from aiobinance.model.order import LimitOrder
from aiobinance.trader import Trader


@pytest.mark.vcr(
    filter_headers=["X-MBX-APIKEY"], filter_query_parameters=["timestamp", "signature"]
)
def test_buy_test(keyfile):
    """ have the trader buy something """

    api = Binance(credentials=keyfile)  # we might need private requests here !

    account = retrieve_account(api=api)

    trader = Trader(account=account, market=account.exchange.market["COTIBNB"])

    # Buy test order overpriced => will readjust !
    # Decimal of float here to test precision. it should be built from string instead !
    order = trader.buy(amount=Decimal(300), total_expected=Decimal(0.45), test=True)
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
        "0.00142200"
    )  # calculated price from expectation & readjusted, at correct precision.
    assert order.side == "BUY"
    assert order.status == "TEST"
    assert order.symbol == "COTIBNB"
    assert order.timeInForce == "GTC"

    # transac time has a dynamic value because it does not depend on recorded traffic !
    # This is measuring with second precision a time in ms
    assert order.transactTime // 1000 == int(datetime.now(tz=timezone.utc).timestamp())

    # Buy test order underpriced
    # Note: it seems that PRICE_FILTER can prevent passing buy orders too far from current price...
    # Decimal of float here to test precision. it should be built from string instead !
    order = trader.buy(amount=Decimal(300), total_expected=Decimal(0.42), test=True)
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
        "0.00140000"
    )  # calculated price from expectation, with correct precision.
    assert order.side == "BUY"
    assert order.status == "TEST"
    assert order.symbol == "COTIBNB"
    assert order.timeInForce == "GTC"

    # transac time has a dynamic value because it does not depend on recorded traffic !
    # This is measuring with second precision a time in ms
    assert order.transactTime // 1000 == int(datetime.now(tz=timezone.utc).timestamp())


@pytest.mark.skip  # skip this while market is not in our interest... recording TODO
@pytest.mark.vcr(
    filter_headers=["X-MBX-APIKEY"], filter_query_parameters=["timestamp", "signature"]
)
def test_buy(keyfile):
    """ have the trader buy something """

    api = Binance(credentials=keyfile)  # we might need private requests here !

    account = retrieve_account(api=api)

    trader = Trader(account=account, market=account.exchange.market["COTIBNB"])

    print("Buy test order: ")
    # Decimal of float here to test precision. it should be built from string instead !
    order = trader.buy(amount=Decimal(300), total_expected=Decimal(0.45), test=False)
    print(order)

    assert order


@pytest.mark.vcr(
    filter_headers=["X-MBX-APIKEY"], filter_query_parameters=["timestamp", "signature"]
)
def test_sell_test(keyfile):
    """ have the trader buy something """

    api = Binance(credentials=keyfile)  # we might need private requests here !

    account = retrieve_account(api=api)

    trader = Trader(account=account, market=account.exchange.market["COTIBNB"])

    # Sell test order overpriced
    # Decimal of float here to test precision. it should be built from string instead !
    order = trader.sell(amount=Decimal(300), total_expected=Decimal(0.45), test=True)
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
    assert order.side == "SELL"
    assert order.status == "TEST"
    assert order.symbol == "COTIBNB"
    assert order.timeInForce == "GTC"

    # transac time has a dynamic value because it does not depend on recorded traffic !
    # This is measuring with second precision a time in ms
    assert order.transactTime // 1000 == int(datetime.now(tz=timezone.utc).timestamp())

    # Sell test order underpriced => will readjust !
    # Decimal of float here to test precision. it should be built from string instead !
    order = trader.sell(amount=Decimal(300), total_expected=Decimal(0.40), test=True)
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
    assert order.side == "SELL"
    assert order.status == "TEST"
    assert order.symbol == "COTIBNB"
    assert order.timeInForce == "GTC"

    # transac time has a dynamic value because it does not depend on recorded traffic !
    # This is measuring with second precision a time in ms
    assert order.transactTime // 1000 == int(datetime.now(tz=timezone.utc).timestamp())


@pytest.mark.skip  # skip this while market is not in our interest... recording TODO
@pytest.mark.vcr(
    filter_headers=["X-MBX-APIKEY"], filter_query_parameters=["timestamp", "signature"]
)
def test_sell(keyfile):
    """ have the trader buy something """

    api = Binance(credentials=keyfile)  # we might need private requests here !

    account = retrieve_account(api=api)

    trader = Trader(account=account, market=account.exchange.market["COTIBNB"])

    print("Sell test order: ")
    # Decimal of float here to test precision. it should be built from string instead !
    order = trader.sell(amount=Decimal(300), total_expected=Decimal(0.45), test=False)
    print(order)

    assert order


if __name__ == "__main__":
    pytest.main(["-s", __file__, "--block-network"])
    # record run
    # pytest.main(['-s', __file__, '--with-keyfile', '--record-mode=new_episodes'])

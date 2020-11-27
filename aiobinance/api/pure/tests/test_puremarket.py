import unittest
from datetime import datetime, timezone
from decimal import Decimal

import hypothesis.strategies as st
from hypothesis import Verbosity, given, settings

from aiobinance.api.pure.puremarket import PureMarket
from aiobinance.model.order import LimitOrder, MarketOrder, OrderSide


class TestPureMarket(unittest.TestCase):
    @given(pm=PureMarket.strategy())
    @settings(verbosity=Verbosity.verbose)
    def test_strategy(self, pm):

        assert isinstance(pm, PureMarket)

    @given(
        pm=PureMarket.strategy(),
        side=OrderSide.strategy(),
        qty=st.decimals(allow_nan=False, allow_infinity=False),
    )
    def test_market_order_base(self, pm, side, qty):

        # now_secs = int(datetime.now(tz=timezone.utc).timestamp())
        sent, order = pm.market_order_base(side=side, quantity=qty)

        assert sent["symbol"] == pm.symbol, f"{sent['symbol']} != {pm.symbol}"
        assert sent["side"] == side.value, f"{sent['side']} != {side.value}"
        assert sent["type"] == "MARKET", f"{sent['type']} != 'MARKET'"

        rounded_qty = "{:0.0{}f}".format(qty, pm.base_asset_precision)
        assert Decimal(sent["quantity"]) == Decimal(
            rounded_qty
        ), f"{Decimal(sent['quantity'])} != {Decimal(rounded_qty)}"

        assert isinstance(
            order, MarketOrder
        ), f"{order} is not an instance of MarketOrder"
        assert (
            order.cummulativeQuoteQty.is_zero()
        ), f"{order.cummulativeQuoteQty} is not zero"
        assert order.executedQty.is_zero(), f"{order.executedQty} is not zero"
        assert order.fills == [], f"{order.fills} != []"
        assert order.order_id == -1, f"{order.order_id} != -1"
        assert order.order_list_id == -1, f"{order.order_list_id} != -1"

        # careful with rounding here as well
        assert order.origQty == Decimal(
            rounded_qty
        ), f"{order.origQty} != {Decimal(rounded_qty)}"

        assert order.side == side, f"{order.side} != {side}"
        assert order.status == "TEST", f"{order.status} != 'TEST'"
        assert order.symbol == pm.symbol, f"{order.status} != {pm.symbol}"
        assert order.type == "MARKET", f"{order.type} != 'MARKET'"

        # too flaky (test must run in < 1sec), disabling
        # assert (
        #     order.transactTime // 1000 == now_secs
        # ), f"{order.transactTime // 1000} != {now_secs}"

    @given(
        pm=PureMarket.strategy(),
        side=OrderSide.strategy(),
        qty=st.decimals(allow_nan=False, allow_infinity=False),
    )
    def test_market_order_quote(self, pm, side, qty):
        raise unittest.SkipTest(
            "Not implemented just yet... but maybe we should get rid of all market orders ?"
        )

        sent, order = pm.market_order_quote(side=side, quantity=qty)

    @given(
        pm=PureMarket.strategy(),
        side=OrderSide.strategy(),
        qty=st.decimals(allow_nan=False, allow_infinity=False),
        price=st.decimals(allow_nan=False, allow_infinity=False),
    )
    def test_limit_order(self, pm, side, qty, price):

        # now_secs = int(datetime.now(tz=timezone.utc).timestamp())
        sent, order = pm.limit_order(side=side, quantity=qty, price=price)

        assert sent["symbol"] == pm.symbol, f"{sent['symbol']} != {pm.symbol}"
        assert sent["side"] == side.value, f"{sent['side']} != {side.value}"
        assert sent["type"] == "LIMIT", f"{sent['type']} != 'LIMIT'"
        assert sent["timeInForce"] == "GTC", f"{sent['timeInForce']} != 'GTC'"

        rounded_qty = "{:0.0{}f}".format(qty, pm.base_asset_precision)
        assert Decimal(sent["quantity"]) == Decimal(
            rounded_qty
        ), f"{Decimal(sent['quantity'])} != {Decimal(rounded_qty)}"

        rounded_price = "{:0.0{}f}".format(price, pm.quote_asset_precision)
        assert Decimal(sent["price"]) == Decimal(
            rounded_price
        ), f"{Decimal(sent['price'])} != {Decimal(rounded_price)}"

        assert isinstance(
            order, LimitOrder
        ), f"{order} is not an instance of LimitOrder"
        assert (
            order.cummulativeQuoteQty.is_zero()
        ), f"{order.cummulativeQuoteQty} is not zero"
        assert order.executedQty.is_zero(), f"{order.executedQty} is not zero"
        assert order.fills == [], f"{order.fills} != []"
        assert order.icebergQty is None, f"{order.icebergQty} is not None"
        assert order.order_id == -1, f"{order.order_id} != -1"
        assert order.order_list_id == -1, f"{order.order_list_id} != -1"

        # careful with rounding here as well
        assert order.origQty == Decimal(
            rounded_qty
        ), f"{order.origQty} != {Decimal(rounded_qty)}"
        assert order.price == Decimal(
            rounded_price
        ), f"{order.price} != {Decimal(rounded_price)}"

        assert order.side == side, f"{order.side} != {side}"
        assert order.status == "TEST", f"{order.status} != 'TEST'"
        assert order.symbol == pm.symbol, f"{order.symbol} != {pm.symbol}"
        assert order.timeInForce == "GTC", f"{order.timeInForce} != 'GTC'"
        assert order.type == "LIMIT", f"{order.type} != 'LIMIT'"

        # too flaky (test must run in < 1sec), disabling
        # assert (
        #     order.transactTime // 1000 == now_secs
        # ), f"{order.transactTime // 1000} != {now_secs}"

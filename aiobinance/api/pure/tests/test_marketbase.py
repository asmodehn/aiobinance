import unittest
from datetime import datetime, timezone
from decimal import Decimal

import hypothesis.strategies as st
from hypothesis import Verbosity, given, settings

from aiobinance.api.model.order import LimitOrder, MarketOrder, OrderSide
from aiobinance.api.pure.marketbase import MarketBase


class TestPureMarket(unittest.TestCase):
    @given(pm=MarketBase.strategy())
    # @settings(verbosity=Verbosity.verbose)
    def test_strategy(self, pm):

        assert isinstance(pm, MarketBase)

    @given(
        pm=MarketBase.strategy(),
        side=OrderSide.strategy(),
        qty=st.decimals(allow_nan=False, allow_infinity=False),
        price=st.decimals(allow_nan=False, allow_infinity=False),
    )
    def test_limit_order(self, pm, side, qty, price):

        # now_secs = int(datetime.now(tz=timezone.utc).timestamp())
        order = pm.limit_order(side=side, quantity=qty, price=price).value

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
        rounded_qty = "{:0.0{}f}".format(qty, pm.info.base_asset_precision)
        assert order.origQty == Decimal(
            rounded_qty
        ), f"{order.origQty} != {Decimal(rounded_qty)}"

        rounded_price = "{:0.0{}f}".format(price, pm.info.quote_asset_precision)
        assert order.price == Decimal(
            rounded_price
        ), f"{order.price} != {Decimal(rounded_price)}"

        assert order.side == side, f"{order.side} != {side}"
        assert order.status == "TEST", f"{order.status} != 'TEST'"
        assert order.symbol == pm.info.symbol, f"{order.symbol} != {pm.info.symbol}"
        assert order.timeInForce == "GTC", f"{order.timeInForce} != 'GTC'"
        assert order.type == "LIMIT", f"{order.type} != 'LIMIT'"

        # too flaky (test must run in < 1sec), disabling
        # assert (
        #     order.transactTime // 1000 == now_secs
        # ), f"{order.transactTime // 1000} != {now_secs}"

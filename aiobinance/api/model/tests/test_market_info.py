import unittest
from decimal import Decimal

import hypothesis.strategies as st
from hypothesis import Verbosity, given, settings

from aiobinance.api.model.market_info import MarketInfo
from aiobinance.api.model.order import OrderSide
from aiobinance.api.pure.puremarket import PureMarket


class TestMarketInfo(unittest.TestCase):
    @given(pm=PureMarket.strategy())
    # @settings(verbosity=Verbosity.verbose)
    def test_strategy(self, pm):

        assert isinstance(pm, PureMarket)

    @given(
        mi=MarketInfo.strategy(),
        side=OrderSide.strategy(),
        qty=st.decimals(allow_nan=False, allow_infinity=False),
        price=st.decimals(allow_nan=False, allow_infinity=False),
    )
    def test_limit_order_params(self, mi, side, qty, price):

        # now_secs = int(datetime.now(tz=timezone.utc).timestamp())
        sent = mi._limit_order_params(side=side, quantity=qty, price=price)

        assert sent["symbol"] == mi.symbol, f"{sent['symbol']} != {mi.symbol}"
        assert sent["side"] == side.value, f"{sent['side']} != {side.value}"
        assert sent["type"] == "LIMIT", f"{sent['type']} != 'LIMIT'"
        assert sent["timeInForce"] == "GTC", f"{sent['timeInForce']} != 'GTC'"

        rounded_qty = "{:0.0{}f}".format(qty, mi.base_asset_precision)
        assert Decimal(sent["quantity"]) == Decimal(
            rounded_qty
        ), f"{Decimal(sent['quantity'])} != {Decimal(rounded_qty)}"

        rounded_price = "{:0.0{}f}".format(price, mi.quote_asset_precision)
        assert Decimal(sent["price"]) == Decimal(
            rounded_price
        ), f"{Decimal(sent['price'])} != {Decimal(rounded_price)}"

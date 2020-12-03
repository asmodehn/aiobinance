import dataclasses
import unittest

import hypothesis.strategies as st
from hypothesis import given

from aiobinance.api.model.trade import Trade


class TestTrade(unittest.TestCase):
    @given(trade=Trade.strategy())
    def test_str(self, trade: Trade):
        # Check sensible information is displayed (order doesnt matter for output to human)
        trade_str = str(trade)
        assert f"time: {str(trade.time)}" in trade_str
        assert f"symbol: {str(trade.symbol)}" in trade_str
        assert f"id: {str(trade.id)}" in trade_str
        assert f"price: {str(trade.price)}" in trade_str
        assert f"qty: {str(trade.qty)}" in trade_str
        assert f"quote_qty: {str(trade.quote_qty)}" in trade_str
        assert (
            f"commission: {str(trade.commission)} {trade.commission_asset}" in trade_str
        )
        assert f"is_buyer: {str(trade.is_buyer)}" in trade_str
        assert f"is_maker: {str(trade.is_maker)}" in trade_str
        assert f"order_id: {str(trade.order_id)}" in trade_str
        assert f"order_list_id: {str(trade.order_list_id)}" in trade_str
        assert f"is_best_match: {str(trade.is_best_match)}" in trade_str

    @given(trade=Trade.strategy())
    def test_dir(self, trade: Trade):
        # check all information is exposed
        expected = {
            "time",
            "symbol",
            "id",
            "price",
            "qty",
            "quote_qty",
            "commission",
            "commission_asset",
            "is_buyer",
            "is_maker",
            "order_id",
            "order_list_id",
            "is_best_match",
        }
        assert {a for a in dir(trade)}.issuperset(expected), expected.difference(
            {a for a in dir(trade)}
        )

        # check no extra information is exposed
        assert {a for a in dir(trade) if not a.startswith("__")}.issubset(expected), {
            a for a in dir(trade) if not a.startswith("__")
        }.difference(expected)


if __name__ == "__main__":
    unittest.main()

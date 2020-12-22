import dataclasses
import unittest
from decimal import Decimal

import hypothesis.strategies as st
from hypothesis import given

from aiobinance.api.model.pricecandle import PriceCandle

# bad strategy : Ref : https://hypothesis.readthedocs.io/en/latest/data.html?#hypothesis.strategies.from_type


class TestPriceCandle(unittest.TestCase):
    @given(candle=PriceCandle.strategy())
    def test_strategy(self, candle: PriceCandle):
        # validating init

        # validating strategy
        assert candle.open_time < candle.close_time

        assert candle.high >= candle.open
        assert candle.high >= candle.close

        assert candle.low <= candle.open
        assert candle.low <= candle.close

        assert candle.volume >= Decimal(0)
        assert candle.num_trades >= Decimal(0)
        assert candle.taker_base_vol >= Decimal(0)
        assert candle.taker_quote_vol >= Decimal(0)

    # TODO : test dtypes

    @given(candle=PriceCandle.strategy())
    def test_str(self, candle: PriceCandle):
        # Check sensible information is displayed (order doesnt matter for output to human)
        candle_str = str(candle)
        assert f"open_time: {str(candle.open_time)}" in candle_str
        assert f"open: {str(candle.open)}" in candle_str
        assert f"high: {str(candle.high)}" in candle_str
        assert f"low: {str(candle.low)}" in candle_str
        assert f"close: {str(candle.close)}" in candle_str
        assert f"volume: {str(candle.volume)}" in candle_str
        assert f"close_time: {str(candle.close_time)}" in candle_str
        assert f"qav: {str(candle.qav)}" in candle_str
        assert f"num_trades: {str(candle.num_trades)}" in candle_str
        assert f"taker_base_vol: {str(candle.taker_base_vol)}" in candle_str
        assert f"taker_quote_vol: {str(candle.taker_quote_vol)}" in candle_str
        assert f"is_best_match: {str(candle.is_best_match)}" in candle_str

    @given(candle=PriceCandle.strategy())
    def test_dir(self, candle: PriceCandle):
        # check all information is exposed
        expected = {
            "open_time",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "close_time",
            "qav",
            "num_trades",
            "taker_base_vol",
            "taker_quote_vol",
            "is_best_match",
        }
        assert {a for a in dir(candle)}.issuperset(expected), expected.difference(
            {a for a in dir(candle)}
        )

        # check no extra information is exposed
        assert {a for a in dir(candle) if not a.startswith("__")}.issubset(expected), {
            a for a in dir(candle) if not a.startswith("__")
        }.difference(expected)


if __name__ == "__main__":
    unittest.main()

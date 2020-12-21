import dataclasses
import unittest
from decimal import Decimal

import hypothesis.strategies as st
from hypothesis import given

from aiobinance.api.model.pricecandle import MinutePriceCandle, PriceCandle


class TestPriceCandle(unittest.TestCase):
    @given(candle=PriceCandle.strategy())
    def test_strategy(self, candle: PriceCandle):
        # validating init

        # validating strategy
        assert candle.volume >= Decimal(0)
        assert candle.num_trades >= Decimal(0)
        assert candle.taker_base_vol >= Decimal(0)
        assert candle.taker_quote_vol >= Decimal(0)

    # TODO : test dtypes

    @given(candle=PriceCandle.strategy())
    def test_str(self, candle: PriceCandle):
        # Check sensible information is displayed (order doesnt matter for output to human)
        candle_str = str(candle)
        assert f"open: {str(candle.open)}" in candle_str
        assert f"high: {str(candle.high)}" in candle_str
        assert f"low: {str(candle.low)}" in candle_str
        assert f"close: {str(candle.close)}" in candle_str
        assert f"volume: {str(candle.volume)}" in candle_str
        assert f"qav: {str(candle.qav)}" in candle_str
        assert f"num_trades: {str(candle.num_trades)}" in candle_str
        assert f"taker_base_vol: {str(candle.taker_base_vol)}" in candle_str
        assert f"taker_quote_vol: {str(candle.taker_quote_vol)}" in candle_str
        assert f"is_best_match: {str(candle.is_best_match)}" in candle_str

    @given(candle=PriceCandle.strategy())
    def test_dir(self, candle: PriceCandle):
        # check all information is exposed
        expected = {
            "open",
            "high",
            "low",
            "close",
            "volume",
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

    @given(candle1=PriceCandle.strategy(), candle2=PriceCandle.strategy())
    def test_lt(self, candle1: PriceCandle, candle2: PriceCandle):
        lt = candle1 < candle2

        assert lt is (
            candle1.num_trades < candle2.num_trades
            or candle1.volume < candle2.volume
            or (candle1.high < candle2.high and candle1.low >= candle2.low)
            or (candle1.high <= candle2.high and candle1.low > candle2.low)
        )

    @given(candle1=PriceCandle.strategy(), candle2=PriceCandle.strategy())
    def test_gt(self, candle1: PriceCandle, candle2: PriceCandle):
        gt = candle1 > candle2
        assert gt is (
            candle1.num_trades > candle2.num_trades
            or candle1.volume > candle2.volume
            or (candle1.high > candle2.high and candle1.low <= candle2.low)
            or (candle1.high >= candle2.high and candle1.low < candle2.low)
        )


class TestMinutePriceCandle(unittest.TestCase):
    @given(candle=MinutePriceCandle.strategy())
    def test_strategy(self, candle: MinutePriceCandle):

        # validating strategy
        assert candle.volume >= Decimal(0)
        assert candle.num_trades >= Decimal(0)
        assert candle.taker_base_vol >= Decimal(0)
        assert candle.taker_quote_vol >= Decimal(0)

        # validating init
        copycandle = MinutePriceCandle(open_time=candle.open_time, price_=candle.price_)
        assert copycandle == candle

        # another kind of init
        copycandle2 = MinutePriceCandle(
            open_time=candle.open_time,
            close_time=candle.close_time,
            # TODO : we should probably rely on somethng in PRiceCandle (vars ? dir ?)
            open=candle.open,
            high=candle.high,
            low=candle.low,
            close=candle.close,
            volume=candle.volume,
            qav=candle.qav,
            num_trades=candle.num_trades,
            taker_base_vol=candle.taker_base_vol,
            taker_quote_vol=candle.taker_quote_vol,
            # for this we go via price_ ... good idea or not ?
            is_best_match=candle.price_.is_best_match,
            # TODO : we should make this idea/behavior precise (cf. datacrystals)
        )
        assert copycandle2 == candle

    # TODO : test dtypes

    @given(candle=MinutePriceCandle.strategy())
    def test_str(self, candle: MinutePriceCandle):
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

    @given(candle=MinutePriceCandle.strategy())
    def test_dir(self, candle: MinutePriceCandle):
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
        }
        assert {a for a in dir(candle)}.issuperset(expected), expected.difference(
            {a for a in dir(candle)}
        )

        # check no extra information is exposed
        assert {a for a in dir(candle) if not a.startswith("__")}.issubset(expected), {
            a for a in dir(candle) if not a.startswith("__")
        }.difference(expected)

    @given(candle1=MinutePriceCandle.strategy(), candle2=MinutePriceCandle.strategy())
    def test_lt(self, candle1: MinutePriceCandle, candle2: MinutePriceCandle):

        lt = candle1 < candle2

        if (
            candle1.open_time != candle2.open_time
            or candle1.close_time != candle2.close_time
        ):
            assert lt is None
        else:
            assert lt is (candle1.price_ < candle2.price_)

    @given(candle1=MinutePriceCandle.strategy(), candle2=MinutePriceCandle.strategy())
    def test_gt(self, candle1: MinutePriceCandle, candle2: MinutePriceCandle):

        lt = candle1 > candle2

        if (
            candle1.open_time != candle2.open_time
            or candle1.close_time != candle2.close_time
        ):
            assert lt is None
        else:
            assert lt is (candle1.price_ > candle2.price_)


# TODO: HourlyPriceCandle / DailyPriceCandle / WeeklyPriceCandle


if __name__ == "__main__":
    unittest.main()

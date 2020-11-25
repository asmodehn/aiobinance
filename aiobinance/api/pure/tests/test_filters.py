import unittest

from hypothesis import Verbosity, given, settings

from aiobinance.api.pure.filters import (
    ExchangeMaxAlgoOrders,
    ExchangeMaxNumOrders,
    Filter,
    IcebergParts,
    LotSize,
    MarketLotSize,
    MaxNumAlgoOrders,
    MaxNumIcebergOrders,
    MaxNumOrders,
    MaxPosition,
    MinNotional,
    PercentPrice,
    PriceFilter,
)


class TestPriceFilter(unittest.TestCase):
    @given(fltr=PriceFilter.strategy())
    @settings(verbosity=Verbosity.verbose)
    def test_strategy(self, fltr):

        assert isinstance(fltr, Filter)
        assert isinstance(fltr, PriceFilter)


class TestPercentPrice(unittest.TestCase):
    @given(fltr=PercentPrice.strategy())
    @settings(verbosity=Verbosity.verbose)
    def test_strategy(self, fltr):

        assert isinstance(fltr, Filter)
        assert isinstance(fltr, PercentPrice)


class TestLotSize(unittest.TestCase):
    @given(fltr=LotSize.strategy())
    @settings(verbosity=Verbosity.verbose)
    def test_strategy(self, fltr):

        assert isinstance(fltr, Filter)
        assert isinstance(fltr, LotSize)


class TestMinNotional(unittest.TestCase):
    @given(fltr=MinNotional.strategy())
    @settings(verbosity=Verbosity.verbose)
    def test_strategy(self, fltr):

        assert isinstance(fltr, Filter)
        assert isinstance(fltr, MinNotional)


class TestIcebergParts(unittest.TestCase):
    @given(fltr=IcebergParts.strategy())
    @settings(verbosity=Verbosity.verbose)
    def test_strategy(self, fltr):

        assert isinstance(fltr, Filter)
        assert isinstance(fltr, IcebergParts)


class TestMarketLotSize(unittest.TestCase):
    @given(fltr=MarketLotSize.strategy())
    @settings(verbosity=Verbosity.verbose)
    def test_strategy(self, fltr):

        assert isinstance(fltr, Filter)
        assert isinstance(fltr, MarketLotSize)


class TestMaxNumOrders(unittest.TestCase):
    @given(fltr=MaxNumOrders.strategy())
    @settings(verbosity=Verbosity.verbose)
    def test_strategy(self, fltr):

        assert isinstance(fltr, Filter)
        assert isinstance(fltr, MaxNumOrders)


class TestMaxNumAlgoOrders(unittest.TestCase):
    @given(fltr=MaxNumAlgoOrders.strategy())
    @settings(verbosity=Verbosity.verbose)
    def test_strategy(self, fltr):

        assert isinstance(fltr, Filter)
        assert isinstance(fltr, MaxNumAlgoOrders)


class TestMaxNumIcebergOrders(unittest.TestCase):
    @given(fltr=MaxNumIcebergOrders.strategy())
    @settings(verbosity=Verbosity.verbose)
    def test_strategy(self, fltr):

        assert isinstance(fltr, Filter)
        assert isinstance(fltr, MaxNumIcebergOrders)


class TestMaxPosition(unittest.TestCase):
    @given(fltr=MaxPosition.strategy())
    @settings(verbosity=Verbosity.verbose)
    def test_strategy(self, fltr):

        assert isinstance(fltr, Filter)
        assert isinstance(fltr, MaxPosition)


class TestExchangeMaxNumOrders(unittest.TestCase):
    @given(fltr=ExchangeMaxNumOrders.strategy())
    @settings(verbosity=Verbosity.verbose)
    def test_strategy(self, fltr):

        assert isinstance(fltr, Filter)
        assert isinstance(fltr, ExchangeMaxNumOrders)


class TestExchangeMaxAlgoOrders(unittest.TestCase):
    @given(fltr=ExchangeMaxAlgoOrders.strategy())
    @settings(verbosity=Verbosity.verbose)
    def test_strategy(self, fltr):

        assert isinstance(fltr, Filter)
        assert isinstance(fltr, ExchangeMaxAlgoOrders)


if __name__ == "__main__":
    unittest.main()

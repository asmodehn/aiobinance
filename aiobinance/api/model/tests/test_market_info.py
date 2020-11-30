import unittest
from datetime import datetime, timezone
from decimal import Decimal

import hypothesis.strategies as st
from hypothesis import Verbosity, given, settings

from aiobinance.api.model.order import LimitOrder, MarketOrder, OrderSide
from aiobinance.api.pure.puremarket import PureMarket


class TestMarketInfo(unittest.TestCase):
    @given(pm=PureMarket.strategy())
    # @settings(verbosity=Verbosity.verbose)
    def test_strategy(self, pm):

        assert isinstance(pm, PureMarket)

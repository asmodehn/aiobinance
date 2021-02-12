import unittest

import hypothesis.strategies as st
from hypothesis import Verbosity, given, settings

from aiobinance.api.model.order import OrderSide


class TestOrderSide(unittest.TestCase):
    @given(os=OrderSide.strategy())
    # @settings(verbosity=Verbosity.verbose)
    def test_strategy(self, os):

        assert isinstance(os, OrderSide)

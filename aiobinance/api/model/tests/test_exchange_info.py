import unittest

import hypothesis.strategies as st
from hypothesis import Verbosity, given, settings

from aiobinance.api.model.exchange_info import ExchangeInfo


class TestExchangeInfo(unittest.TestCase):
    @given(ei=ExchangeInfo.strategy())
    # @settings(verbosity=Verbosity.verbose)
    def test_strategy(self, ei):

        assert isinstance(ei, ExchangeInfo)

import asyncio
import unittest
from datetime import MINYEAR, datetime, timedelta, timezone
from decimal import Decimal

import hypothesis.strategies as st
from hypothesis import Verbosity, given, settings

from aiobinance.api.mock.mockmarket import MockMarket
from aiobinance.api.model.market_info import MarketInfo


class TestMockMarket(unittest.TestCase):
    @given(data=st.data())
    def test_init(self, data):
        me = data.draw(MockMarket.strategy())
        assert isinstance(me, MockMarket)


if __name__ == "__main__":
    unittest.main()

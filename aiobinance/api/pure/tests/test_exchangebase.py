import asyncio
import unittest
from datetime import MINYEAR, datetime, timezone

import hypothesis.strategies as st
from hypothesis import given

from aiobinance.api.model.exchange_info import ExchangeInfo
from aiobinance.api.pure.exchangebase import ExchangeBase
from aiobinance.api.pure.marketbase import MarketBase


class TestExchangeBase(unittest.TestCase):
    @given(data=st.data())
    def test_init(self, data):
        eb = data.draw(ExchangeBase.strategy())
        if eb.info is None:
            assert eb.servertime == datetime(
                year=MINYEAR, month=1, day=1, tzinfo=timezone.utc
            )
            assert eb.markets == {}
        else:
            # asserting that the init value is reflected properly
            assert eb.servertime == eb.info.servertime
            assert eb.markets == {s.symbol: MarketBase(info=s) for s in eb.info.symbols}

    @given(eb=ExchangeBase.strategy(), info_update=ExchangeInfo.strategy())
    def test_call_update(self, eb: ExchangeBase, info_update: ExchangeInfo):

        asyncio.run(eb(info=info_update))

        # asserting that the new value is reflected properly
        assert eb.servertime == info_update.servertime
        assert eb.markets == {s.symbol: MarketBase(info=s) for s in info_update.symbols}

        with self.assertRaises(NotImplementedError):
            asyncio.run(eb())


if __name__ == "__main__":
    unittest.main()

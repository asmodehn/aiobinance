import unittest
from datetime import MINYEAR, datetime

import hypothesis.strategies as st
from hypothesis import given

from aiobinance.api.model.exchange_info import ExchangeInfo
from aiobinance.api.pure.exchangebase import ExchangeBase
from aiobinance.api.pure.puremarket import PureMarket


class TestExchangeBase(unittest.TestCase):
    @given(data=st.data())
    def test_init(self, data):
        eb = data.draw(ExchangeBase.strategy())
        if eb.info is None:
            assert eb.servertime == datetime(year=MINYEAR, month=1, day=1)
            assert eb.markets == {}
        else:
            # asserting that the init value is reflected properly
            assert eb.servertime == eb.info.servertime
            assert eb.markets == {s.symbol: PureMarket(info=s) for s in eb.info.symbols}

    @given(eb=ExchangeBase.strategy(), info_update=ExchangeInfo.strategy())
    def test_call_update(self, eb: ExchangeBase, info_update: ExchangeInfo):

        eb(info=info_update)
        # asserting that the new value is reflected properly
        assert eb.servertime == info_update.servertime
        assert eb.markets == {s.symbol: PureMarket(info=s) for s in info_update.symbols}


if __name__ == "__main__":
    unittest.main()

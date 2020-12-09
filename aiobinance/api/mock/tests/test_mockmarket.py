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

    # # ONLY positive time delta for real life usecase...
    # @given(
    #     me=MockMarket.strategy(),
    #     update_delta=st.timedeltas(min_value=timedelta(microseconds=1)),
    #     info_update=st.one_of(st.none(), MarketInfo.strategy()),
    # )
    # def test_call_update(
    #     self, me: MockMarket, update_delta: timedelta, info_update: MarketInfo
    # ):
    #     # because hypothesis and unittest async dont go together just yet: https://github.com/HypothesisWorks/hypothesis/issues/2514
    #     async def asyncrun():
    #
    #         if info_update is not None:  # simple test
    #
    #             await me(update_delta=update_delta, info=info_update)
    #             assert me.info == info_update
    #
    #         else:
    #             try:  # if time is going to overflow : no change.
    #                 old_servertime + update_delta
    #             except OverflowError:
    #                 await me(update_delta=update_delta, info=info_update)
    #             else:
    #                 await me(update_delta=update_delta, info=info_update)
    #
    #     asyncio.run(asyncrun())


if __name__ == "__main__":
    unittest.main()

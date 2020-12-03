import asyncio
import unittest
from datetime import MINYEAR, datetime, timedelta, timezone
from decimal import Decimal

import hypothesis.strategies as st
from hypothesis import Verbosity, given, settings

from aiobinance.api.mock.market import MockMarket
from aiobinance.api.mock.mockexchange import MockExchange
from aiobinance.api.model.exchange_info import ExchangeInfo


class TestMockExchange(unittest.IsolatedAsyncioTestCase):
    @given(data=st.data())
    def test_init(self, data):
        me = data.draw(MockExchange.strategy())
        if me.info is None:
            assert me.servertime == datetime(year=MINYEAR, month=1, day=1)
            assert me.markets == {}
        else:
            # asserting that the init value is reflected properly
            assert me.servertime == me.info.servertime
            assert me.markets == {s.symbol: MockMarket(info=s) for s in me.info.symbols}

    # ONLY positive time delta for real life usecase...
    @given(
        me=MockExchange.strategy(),
        update_delta=st.timedeltas(min_value=timedelta(microseconds=1)),
        info_update=st.one_of(st.none(), ExchangeInfo.strategy()),
    )
    def test_call_update(
        self, me: MockExchange, update_delta: timedelta, info_update: ExchangeInfo
    ):
        # because hypothesis and unittest async dont go together just yet: https://github.com/HypothesisWorks/hypothesis/issues/2514
        async def asyncrun():
            old_servertime = me.servertime
            old_markets = me.markets

            if info_update is not None:  # simple test

                await me(update_delta=update_delta, info=info_update)
                assert me.info == info_update

                # asserting that the new value is reflected properly by cache in this case
                assert me.servertime == info_update.servertime
                assert me.markets == {
                    s.symbol: MockMarket(info=s) for s in info_update.symbols
                }
            else:
                try:  # if time is going to overflow : no change.
                    old_servertime + update_delta
                except OverflowError:
                    await me(update_delta=update_delta, info=info_update)

                    # asserting that the new value is reflected properly by cache in all other cases
                    assert me.servertime == old_servertime
                    assert me.markets == old_markets
                else:
                    await me(update_delta=update_delta, info=info_update)

                    # asserting that the new value is reflected properly by cache in all other cases
                    assert me.servertime == (old_servertime + update_delta)
                    assert me.markets == old_markets

        asyncio.run(asyncrun())


if __name__ == "__main__":
    unittest.main()

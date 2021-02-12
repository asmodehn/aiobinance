import asyncio
import unittest
from datetime import MINYEAR, datetime, timedelta, timezone
from decimal import Decimal

import hypothesis.strategies as st
from hypothesis import HealthCheck, Verbosity, assume, given, settings

from aiobinance.api.mock.mockexchange import MockExchange
from aiobinance.api.mock.mockmarket import MockMarket
from aiobinance.api.model.exchange_info import ExchangeInfo


class TestMockExchange(unittest.TestCase):
    @given(me=MockExchange.strategy(), data=st.data())
    def test_init(self, me, data):
        if me.info is None:
            assert me.servertime == datetime(
                year=MINYEAR, month=1, day=1, tzinfo=timezone.utc
            )
            assert me.markets == {}
        else:
            # asserting that the init value is reflected properly
            assert me.servertime == me.info.servertime
            assert me.markets == {s.symbol: MockMarket(info=s) for s in me.info.symbols}

    # ONLY positive time delta for real life usecase...
    @given(
        me=MockExchange.strategy(),
        info_update=st.one_of(st.none(), ExchangeInfo.strategy()),
        data=st.data(),
    )
    def test_call_update(self, me: MockExchange, info_update: ExchangeInfo, data):
        # because hypothesis and unittest async dont go together just yet:
        # https://github.com/HypothesisWorks/hypothesis/issues/2514
        async def asyncrun():
            nonlocal me, info_update

            # retrieving updated info before, as time will change again on 'me.__call__()'
            update_delta = data.draw(st.timedeltas(min_value=timedelta(microseconds=1)))
            updated_info = (
                await me.exchangeinfo(update_delta=update_delta)
            ).ok()  # new updated info
            assume(
                updated_info is not None
            )  # this will prevent using update_delta that trigger error (overflow)

            if info_update is None:
                await me(update_delta=update_delta)
                # passing None for info will retrieve _remote_info, but only if needed,
                # and apply various modifications to it.
                assert (
                    me.info is not None
                )  # we cannot willingly erase info via __call__()

            else:
                # in this case there is an exact update (if you want modification applied, you should do it yourself)
                await me(info=info_update, update_delta=update_delta)
                updated_info = (
                    info_update  # Note: update delta will not have any effect here !
                )
            # TODO : assert warning when passing both info and update_delta

            # asserting that the new value is reflected properly by cache in all other cases
            assert me.info == updated_info
            assert me.servertime == updated_info.servertime
            assert me.markets == {
                s.symbol: MockMarket(info=s) for s in updated_info.symbols
            }

        asyncio.run(asyncrun())

    @given(
        me=MockExchange.strategy(),
        update_delta=st.timedeltas(min_value=timedelta(microseconds=1)),
    )
    @settings(suppress_health_check=[HealthCheck.too_slow])
    def test_exchangeinfo(self, me: MockExchange, update_delta: timedelta):
        # because hypothesis and unittest async dont go together just yet:
        # https://github.com/HypothesisWorks/hypothesis/issues/2514
        async def asyncrun():
            nonlocal me, update_delta

            old_info = me._remote_info if me.info is None else me.info

            try:  # if time is going to overflow : exception in result
                old_info.servertime + update_delta
            except OverflowError:
                new_info = await me.exchangeinfo(update_delta=update_delta)
                assert new_info.is_err()
                assert isinstance(new_info.err(), OverflowError)
            else:
                new_info = await me.exchangeinfo(update_delta=update_delta)
                assert new_info.ok() == old_info(update_delta=update_delta)
                # grabbing mandatory info if info is None
                assert new_info.ok().servertime == (old_info.servertime + update_delta)

        asyncio.run(asyncrun())


if __name__ == "__main__":
    unittest.main()

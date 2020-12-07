import unittest
from datetime import MINYEAR, datetime

import hypothesis.strategies as st
from hypothesis import given

from aiobinance.api.model.account_info import AccountInfo
from aiobinance.api.model.exchange_info import ExchangeInfo
from aiobinance.api.pure.accountbase import AccountBase
from aiobinance.api.pure.exchangebase import ExchangeBase
from aiobinance.api.pure.marketbase import MarketBase


class TestAccountBase(unittest.TestCase):
    @given(data=st.data())
    def test_init(self, data):
        ab = data.draw(AccountBase.strategy())
        if ab.info is None:
            assert ab.update_time == datetime(year=MINYEAR, month=1, day=1)
            assert ab.balances == []
        else:
            # asserting that the init value is reflected properly
            assert ab.update_time == ab.info.updateTime
            assert ab.balances == ab.info.balances

    @given(ab=AccountBase.strategy(), info_update=AccountInfo.strategy())
    def test_call_update(self, ab: AccountBase, info_update: AccountInfo):

        ab(info=info_update)
        # asserting that the new value is reflected properly
        assert ab.update_time == info_update.updateTime
        assert ab.balances == ab.info.balances


if __name__ == "__main__":
    unittest.main()

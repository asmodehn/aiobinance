import asyncio
import unittest
from datetime import MINYEAR, datetime
from typing import Dict

import hypothesis.strategies as st
from hypothesis import given

from aiobinance.api.model.account_info import AccountInfo
from aiobinance.api.model.asset_info import AssetInfo
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
            assert ab.balances == {}
        else:
            # asserting that the init value is reflected properly
            assert ab.update_time == ab.info.updateTime
            assert ab.balances == {
                b.asset: b
                for b in ab.info.balances
                if not (b.free.is_zero() and b.locked.is_zero())
            }

    @given(
        ab=AccountBase.strategy(),
        info_update=AccountInfo.strategy(),
        assets_update=st.text(min_size=1, max_size=4).flatmap(
            lambda s: st.dictionaries(
                keys=st.just(s), values=AssetInfo.strategy(coin=s)
            )
        ),
    )
    def test_call_update(
        self,
        ab: AccountBase,
        info_update: AccountInfo,
        assets_update: Dict[str, AssetInfo],
    ):

        asyncio.run(ab(info=info_update, assetsinfo=assets_update))
        # asserting that the new value is reflected properly
        assert ab.update_time == info_update.updateTime
        assert ab.balances == {
            b.asset: b
            for b in ab.info.balances
            if not (b.free.is_zero() and b.locked.is_zero())
        }

        for a in assets_update:
            assert a in ab.ledgers

        with self.assertRaises(NotImplementedError):
            asyncio.run(ab())


if __name__ == "__main__":
    unittest.main()

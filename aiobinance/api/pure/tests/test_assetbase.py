import asyncio
import unittest
from datetime import MINYEAR, datetime
from typing import Dict

import hypothesis.strategies as st
from hypothesis import given

from aiobinance.api.model.account_info import AccountInfo, AssetAmount
from aiobinance.api.model.asset_info import AssetInfo
from aiobinance.api.model.exchange_info import ExchangeInfo
from aiobinance.api.pure.accountbase import AccountBase
from aiobinance.api.pure.assetbase import AssetBase
from aiobinance.api.pure.exchangebase import ExchangeBase
from aiobinance.api.pure.ledgerviewbase import LedgerViewBase
from aiobinance.api.pure.marketbase import MarketBase


class TestAssetBase(unittest.TestCase):
    @given(data=st.data())
    def test_init(self, data):
        ab = data.draw(AssetBase.strategy())
        assert isinstance(ab, AssetBase)

    @given(
        ab=AssetBase.strategy(),
        info_update=AssetInfo.strategy(),
        amount_update=AssetAmount.strategy(),
    )
    def test_call_update(
        self,
        ab: AssetBase,
        info_update: AssetInfo,
        amount_update: AssetAmount,
    ):

        asyncio.run(ab(info=info_update, amount=amount_update))
        # asserting that the new value is reflected properly
        assert ab.info == info_update
        assert ab.amount == amount_update

        with self.assertRaises(NotImplementedError):
            asyncio.run(ab())

    @given(
        ab=AssetBase.strategy(),
    )
    def test_ledgers(self, ab):
        if ab.info is None:
            assert ab.ledger is None
        else:
            ldg = ab.ledger
            assert isinstance(ldg, LedgerViewBase)
            assert ldg.coininfo == ab.info
            assert ldg.base_trades == {m.symbol: m.base_trades for m in ab.base_markets}
            assert ldg.quote_trades == {
                m.symbol: m.quote_trades for m in ab.quote_markets
            }


if __name__ == "__main__":
    unittest.main()

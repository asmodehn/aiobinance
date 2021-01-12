from __future__ import annotations

from dataclasses import dataclass, field
from datetime import MINYEAR, datetime, timedelta
from functools import cached_property
from typing import Dict, List, Optional, Type

import hypothesis.strategies as st
from hypothesis.strategies import SearchStrategy
from result import Err, Result

from aiobinance.api.model.account_info import AccountInfo, AssetAmount
from aiobinance.api.model.asset_info import AssetInfo
from aiobinance.api.pure.ledgerviewbase import LedgerViewBase


@dataclass(frozen=False)
class AccountBase:

    info: Optional[AccountInfo] = field(init=True, default=None)
    # TODO : status : https://binance-docs.github.io/apidocs/spot/en/#account-status-user_data

    assets_info: Optional[Dict[str, AssetInfo]] = field(init=False, default=None)

    @classmethod
    def strategy(
        cls, info=st.one_of(st.none(), AccountInfo.strategy()), **kwargs
    ) -> SearchStrategy:
        return st.builds(cls, info=info)

    @property  # CAREFUL : balances can change each async call
    def update_time(self) -> datetime:  # monotonically increase -> start in the past.
        return (
            self.info.updateTime
            if self.info is not None
            else datetime(year=MINYEAR, month=1, day=1)
        )

    @property  # CAREFUL : balances can change each async call
    def balances(
        self,
    ) -> Dict[str, AssetAmount]:  # monotonically increase -> start in the past.
        return (
            {
                b.asset: b
                for b in self.info.balances
                if not (b.free.is_zero() and b.locked.is_zero())
            }
            if self.info is not None
            else {}
        )

    @cached_property
    def ledgers(self) -> Dict[str, LedgerViewBase]:
        if self.assets_info is None:
            return {}
            # there should be a special case also in child classes
        else:
            ldgrs = {}
            for ai in self.assets_info.values():
                balnc = [
                    b for b in self.info.balances if b.asset == ai.coin
                ]  # assume there is only one
                balnc = (
                    balnc[0] if len(balnc) > 0 else AssetAmount(asset=ai.coin)
                )  # TODO : shall we drop when we have 0 ???
                ldgrs.update({ai.coin: LedgerViewBase(coin=ai, amount=balnc)})
            return ldgrs

    async def __call__(
        self,
        *,
        info: Optional[AccountInfo] = None,
        assetsinfo: Optional[Dict[str, AssetInfo]] = None,
        **kwargs
    ) -> AccountBase:

        if info is None:
            res = await self.accountinfo()
            if res.is_err():
                raise res.err()
            else:
                info = res.ok()

        if assetsinfo is None:
            res = await self.assetsinfo()
            if res.is_err():
                raise res.err()
            else:
                assetsinfo = res.ok()

        self.info = info
        self.assets_info = assetsinfo

        return self

    async def accountinfo(self) -> Result[AccountInfo, NotImplementedError]:
        return Err(NotImplementedError())

    async def assetsinfo(self) -> Result[Dict[str, AssetInfo], NotImplementedError]:
        return Err(NotImplementedError())


if __name__ == "__main__":
    eb = AccountBase.strategy().example()
    print(eb)
    eb_updated = eb(info=AccountInfo.strategy().example())
    print(eb_updated)

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import MINYEAR, datetime, timedelta
from functools import cached_property
from typing import Dict, List, Optional, Type

import hypothesis.strategies as st
from hypothesis.strategies import SearchStrategy
from result import Err, Result

from aiobinance.api.model.account_info import AccountInfo, AssetAmount
from aiobinance.api.model.asset_info import AssetInfo
from aiobinance.api.pure.assetbase import AssetBase
from aiobinance.api.pure.exchangebase import ExchangeBase
from aiobinance.api.pure.ledgerviewbase import LedgerViewBase


@dataclass(frozen=False)
class AccountBase:
    # TODO a way to index subaccount, similar to how markets are indexed by symbol...

    info: Optional[AccountInfo] = field(init=True, default=None)
    # TODO : status : https://binance-docs.github.io/apidocs/spot/en/#account-status-user_data

    assets_info: Dict[str, AssetInfo] = field(init=False, default_factory=dict)
    # TODO : investigate this : not all coins present (BNB? BTC?)
    #  Note this is actually mostly useful for deposit / withdrawal

    # exchange as property as it can be pased as argument
    exchange: Optional[ExchangeBase] = field(init=False, default=None)

    @classmethod
    def strategy(
        cls,
        exchange=st.one_of(st.none(), ExchangeBase.strategy()),
        info=st.one_of(st.none(), AccountInfo.strategy()),
        assets_info=st.text(min_size=1, max_size=4).flatmap(
            lambda ex: st.dictionaries(
                keys=st.just(ex), values=AssetInfo.strategy(coin=ex)
            )
        ),
        **kwargs
    ) -> SearchStrategy:
        return st.builds(cls, info=info)

    def __post_init__(self):
        # Note : Exchange refreshes itself
        if self.exchange is None:
            self.exchange = ExchangeBase()

    @property  # CAREFUL : balances can change each async call
    def update_time(self) -> datetime:  # monotonically increase -> start in the past.
        return (
            self.info.updateTime
            if self.info is not None
            else datetime(year=MINYEAR, month=1, day=1)
        )

    @property
    def interesting_markets(self):
        # TODO : config file to add more assets, but always include assets where we have some amount.
        return {"EUR", "BTC", "ETH", "BCH", "ADA", "XTZ", "DOT"}.union(
            set(self.balances.keys())
        )

    def _markets_with_base(self, asset: str):
        mkts = [  # retrieving tradeview for related markets
            m
            for m in self.exchange.markets.values()
            if (
                asset == m.info.base_asset
                and m.info.quote_asset in self.interesting_markets
            )  # TODO : move this into a config (we want to limit the assets we look at)
        ]
        return mkts

    def _markets_with_quote(self, asset: str):
        mkts = [  # retrieving tradeview for related markets
            m
            for m in self.exchange.markets.values()
            if (
                asset == m.info.quote_asset
                and m.info.base_asset in self.interesting_markets
            )  # TODO : move this into a config (we want to limit the assets we look at)
        ]
        return mkts

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

    @property
    def assets(self) -> Dict[str, AssetBase]:
        # returns all assets, based on assets_info
        return (
            {
                asst: AssetBase(
                    amount=self.balances.get(asst, AssetAmount(asset=asst)),
                    info=ainf,
                    base_markets=[  # retrieving tradeview for related markets
                        m for m in self._markets_with_base(asst)
                    ],
                    quote_markets=[m for m in self._markets_with_quote(asst)],
                )
                for asst, ainf in self.assets_info.items()
            }
            if self.assets_info is not None
            else {}
        )

    async def __call__(
        self,
        *,
        info: Optional[AccountInfo] = None,
        assetsinfo: Optional[Dict[str, AssetInfo]] = None,
        **kwargs
    ) -> AccountBase:

        if self.exchange.info is None:  # TODO : find a better way
            # update exchange if needed (required to retrieve related markets)
            await self.exchange()
        # TODO : only do this if relevant (no data or long time without update)

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
        self.assets_info.update(assetsinfo)  # merge dict (should converge...)

        return self

    async def accountinfo(self) -> Result[AccountInfo, NotImplementedError]:
        return Err(NotImplementedError())

    async def assetsinfo(self) -> Result[Dict[str, AssetInfo], NotImplementedError]:
        return Err(NotImplementedError())


if __name__ == "__main__":
    eb = AccountBase.strategy().example()
    print(eb)
    eb_updated = asyncio.run(
        eb(
            info=AccountInfo.strategy().example(),
            assetsinfo=st.text(min_size=1, max_size=4)
            .flatmap(
                lambda ex: st.dictionaries(
                    keys=st.just(ex), values=AssetInfo.strategy(coin=ex)
                )
            )
            .example(),
        )
    )
    print(eb_updated)

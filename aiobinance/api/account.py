from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from functools import cached_property
from typing import Dict, Optional, Type

from hypothesis.strategies import SearchStrategy
from result import Err, Ok, Result

from aiobinance.api.asset import Asset
from aiobinance.api.exchange import Exchange
from aiobinance.api.model.account_info import AccountInfo, AssetAmount
from aiobinance.api.model.asset_info import AssetInfo, NetworkInfo
from aiobinance.api.pure.accountbase import AccountBase
from aiobinance.api.rawapi import Binance


@dataclass(frozen=False)
class Account(AccountBase):

    """ A class to simplify interacting with binance account through the REST API."""

    api: Binance = field(init=True, default=Binance())
    test: bool = field(init=True, default=True)

    # exchange as property as it can be pased as argument
    exchange: Optional[Exchange] = field(init=False, default=None)

    @classmethod
    def strategy(cls, **kwargs) -> SearchStrategy:
        raise RuntimeError(
            "Strategy should not be used with real implementation. Build an instance from actual data instead."
        )

    def __post_init__(self):
        # Note : Exchange refreshes itself
        if self.exchange is None:
            self.exchange = Exchange(api=self.api, test=self.test)

    @property
    def assets(self) -> Dict[str, Asset]:
        return (
            {
                asst: Asset(
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

    # interactive behavior
    async def accountinfo(self) -> Result[AccountInfo, RuntimeError]:

        if self.api.creds is None:
            return Err(RuntimeError("Credentials not specified !"))

        res = self.api.call_api(command="account")

        if res.is_ok():
            res = res.value
        else:
            # TODO : handle API error properly
            return Err(RuntimeError(res.value))

        # Binance translation is only a matter of binance json -> python data structure && avoid data duplication.
        # We do not want to change the semantics of the exchange exposed models here.
        info = AccountInfo(
            makerCommission=res["makerCommission"],
            takerCommission=res["takerCommission"],
            buyerCommission=res["buyerCommission"],
            sellerCommission=res["sellerCommission"],
            canTrade=res["canTrade"],
            canWithdraw=res["canWithdraw"],
            canDeposit=res["canDeposit"],
            updateTime=res["updateTime"],
            accountType=res["accountType"],  # should be "SPOT"
            balances=res["balances"],
            permissions=res["permissions"],
        )

        # we update the current frozen instance (base class know how to)
        return Ok(info)

    async def assetsinfo(self) -> Result[Dict[str, AssetInfo], RuntimeError]:

        res = self.api.call_api(command="coins")

        if res.is_ok():
            res = res.value
        else:
            # TODO : handle API error properly
            Err(RuntimeError(res.value))

        assets = {}
        for asset in res:
            coin = asset["coin"]
            assert isinstance(coin, str)
            assets.update(
                {
                    coin: AssetInfo(
                        coin=coin,
                        depositAllEnable=asset["depositAllEnable"],
                        withdrawAllEnable=asset["withdrawAllEnable"],
                        name=asset["name"],
                        free=asset["free"],
                        locked=asset["locked"],
                        freeze=asset["freeze"],
                        withdrawing=asset["withdrawing"],
                        ipoing=asset["ipoing"],
                        ipoable=asset["ipoable"],
                        storage=asset["storage"],
                        isLegalMoney=asset["isLegalMoney"],
                        trading=asset["trading"],
                        networkList=[
                            NetworkInfo(
                                network=nw["network"],
                                coin=nw["coin"],
                                withdrawIntegerMultiple=nw["withdrawIntegerMultiple"],
                                isDefault=nw["isDefault"],
                                depositEnable=nw["depositEnable"],
                                withdrawEnable=nw["withdrawEnable"],
                                depositDesc=nw.get("depositDesc"),
                                withdrawDesc=nw.get("withdrawDesc"),
                                specialTips=nw.get("specialTips"),
                                name=nw["name"],
                                resetAddressStatus=nw["resetAddressStatus"],
                                addressRegex=nw["addressRegex"],
                                memoRegex=nw["memoRegex"],
                                withdrawFee=nw["withdrawFee"],
                                withdrawMin=nw["withdrawMin"],
                                withdrawMax=nw[
                                    "withdrawMax"
                                ],  # Note : here 0 seems to mean "no max" ?? (> Min)
                                minConfirm=nw["minConfirm"],
                                unlockConfirm=nw.get("unLockConfirm"),
                            )
                            for nw in asset["networkList"]
                        ],
                    )
                }
            )

        return Ok(assets)


if __name__ == "__main__":

    from aiobinance.config import load_api_keyfile

    api = Binance(credentials=load_api_keyfile())

    # Testing with actual values and network connection here (only retrieving information)
    acc = Account(api=api, test=True)
    now = datetime.now(tz=timezone.utc)

    async def run_accnt():
        global now
        print(f"update_time: {acc.update_time}")
        print(f"now: {now}")

        await acc()

        print(acc)
        print(acc.assets)

    asyncio.run(run_accnt())
    # TODO: some interactive repl to test this...

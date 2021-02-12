import functools
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, List, Optional

from result import Err, Ok, Result

from aiobinance.api.ledgerview import LedgerView
from aiobinance.api.market import Market
from aiobinance.api.model.account_info import AccountInfo, AssetAmount
from aiobinance.api.model.asset_info import AssetInfo, NetworkInfo
from aiobinance.api.model.market_info import MarketInfo
from aiobinance.api.model.order import LimitOrder, MarketOrder, OrderFill, OrderSide
from aiobinance.api.model.pricecandle import PriceCandle
from aiobinance.api.model.trade import Trade
from aiobinance.api.ohlcview import OHLCView
from aiobinance.api.pure.assetbase import AssetBase
from aiobinance.api.pure.marketbase import MarketBase
from aiobinance.api.pure.ticker import Ticker
from aiobinance.api.rawapi import Binance
from aiobinance.api.tradesview import TradesView


@dataclass(frozen=False)
class Asset(AssetBase):
    """A class to simplify interacting with binance assets through the REST API.
    Here we inherit from AssetBase, to get same methods signatures, therefore specifying the same behavior,
     as with AssetBase which we test thoroughly without side effect.
    While leveraging the inheritance relationship as a way to specify behavior of effectful code...
    """

    api: Binance = field(init=True, default=Binance())
    test: bool = field(init=True, default=True)

    base_markets: List[Market] = field(init=True, default_factory=list)
    quote_markets: List[Market] = field(init=True, default_factory=list)

    @property  # Dynamic : might change with balance...
    def ledger(self) -> LedgerView:
        # TODO : find all related Market symbol, and request trades for these...

        return LedgerView(
            api=self.api,
            coin=self.info,
            base_trades={m.info.symbol: m.trades for m in self.base_markets},
            quote_trades={m.info.symbol: m.trades for m in self.quote_markets},
        )

        # for ai in self.assets_info.values():
        #     balnc = [b for b in self.info.balances if b.asset == ai.coin]
        #
        #     if balnc:  # assume there is only one
        #         ldgrs.update({ai.coin: LedgerView(api=self.api, coin=ai, amount=balnc[0])})
        # return ldgrs

    async def assetinfo(self, **kwargs) -> Result[Dict[str, AssetInfo], RuntimeError]:

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

    async def amountrequest(self, **kwargs) -> Result[AssetAmount, RuntimeError]:
        res = self.api.call_api(command="account")

        if res.is_ok():
            res = res.ok()
        else:
            # TODO : handle API error properly
            Err(RuntimeError(res.err()))

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
        for b in info.balances:
            if b.asset == self.info.coin:
                return Ok(b)
        return Ok(AssetAmount(asset=self.info.coin, free=Decimal(0), locked=Decimal(0)))


if __name__ == "__main__":
    import asyncio

    from aiobinance.config import load_api_keyfile

    api = Binance(credentials=load_api_keyfile())

    ab = Asset(api=api, info=AssetInfo.strategy().example())
    print(ab)

    ab_updated = asyncio.run(ab())
    print(ab_updated)
    # TODO : some interactive repl to test it manually...

from __future__ import annotations

import asyncio
import functools
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

import hypothesis.strategies as st
from hypothesis.strategies import SearchStrategy
from result import Err, Ok, Result

from aiobinance.api.market import Market
from aiobinance.api.model.exchange_info import ExchangeInfo, RateLimit
from aiobinance.api.model.filters import Filter
from aiobinance.api.model.market_info import MarketInfo
from aiobinance.api.pure.exchangebase import ExchangeBase
from aiobinance.api.rawapi import Binance

# converting camel case (API) to snake case (aiobinance)
camel_snake = re.compile(r"(?<!^)(?=[A-Z])")


@dataclass(frozen=False)
class Exchange(ExchangeBase):
    """ A class to simplify interacting with binance exchange through the REST API."""

    api: Binance = field(init=True, default=Binance())
    test: bool = field(init=True, default=True)

    @classmethod
    def strategy(cls, **kwargs) -> SearchStrategy:
        raise RuntimeError(
            "Strategy should not be used with real implementation. Build an instance from actual data instead."
        )

    @property  # not cached ! we have only one instance. And api can change, giving private access to markets.
    def markets(self) -> Dict[str, Market]:
        return (
            {
                s.symbol: Market(api=self.api, info=s, test=self.test)
                for s in self.info.symbols
            }
            if self.info is not None
            else {}
        )

    # TODO : system status : https://binance-docs.github.io/apidocs/spot/en/#system-status-system

    async def exchangeinfo(self) -> Result[ExchangeInfo, RuntimeError]:

        # TODO : implement rate limiting somehow...
        res = self.api.call_api(command="exchangeInfo")

        if res.is_ok():
            res = res.value
        else:
            # TODO : handle API error properly
            return Err(RuntimeError(res.value))

        # timezone mess
        if res["timezone"] == "UTC":
            tz = timezone.utc
        else:
            return Err(RuntimeError("Unknown timezone !"))

        # Binance translation is only a matter of binance json -> python data structure && avoid data duplication.
        # We do not want to change the semantics of the exchange exposed models here.
        info = ExchangeInfo(
            servertime=datetime.fromtimestamp(float(res["serverTime"]) / 1000, tz=tz),
            rate_limits=[
                RateLimit(
                    rate_limit_type=rl["rateLimitType"],
                    interval=rl["interval"],
                    interval_num=rl["intervalNum"],
                    limit=rl["limit"],
                )
                for rl in res["rateLimits"]
            ],
            exchange_filters=[
                Filter(filter_type=f["filterType"]) for f in res["exchangeFilters"]
            ],
            symbols=[
                MarketInfo(
                    symbol=s["symbol"],
                    status=s["status"],
                    base_asset=s["baseAsset"],
                    base_asset_precision=s["baseAssetPrecision"],
                    quote_asset=s["quoteAsset"],
                    quote_precision=s["quotePrecision"],
                    quote_asset_precision=s["quoteAssetPrecision"],
                    base_commission_precision=s["baseCommissionPrecision"],
                    quote_commission_precision=s["quoteCommissionPrecision"],
                    order_types=s["orderTypes"],
                    iceberg_allowed=s["icebergAllowed"],
                    oco_allowed=s["ocoAllowed"],
                    quote_order_qty_market_allowed=s["quoteOrderQtyMarketAllowed"],
                    is_spot_trading_allowed=s["isSpotTradingAllowed"],
                    is_margin_trading_allowed=s["isMarginTradingAllowed"],
                    filters=[
                        Filter.factory(
                            # we also convert the case of the keys...
                            **{
                                camel_snake.sub("_", fk).lower(): fv
                                for fk, fv in f.items()
                            }
                        )
                        for f in s["filters"]
                    ],
                    permissions=s["permissions"],
                )
                for s in res["symbols"]
            ],
        )

        return Ok(info)


if __name__ == "__main__":

    # Testing with actual values and network connection here (only retrieving information)
    ex = Exchange(api=Binance(), test=True)
    now = datetime.now(tz=timezone.utc)

    async def run_exchg():
        global now
        print(f"servertime: {ex.servertime}")
        print(f"now: {now}")

        newnow = datetime.now(tz=timezone.utc)
        await ex()  # update_delta=newnow - now)
        print(f"servertime: {ex.servertime}")
        now = newnow
        print(f"now: {now}")

        await asyncio.sleep(1)

        newnow = datetime.now(tz=timezone.utc)
        await ex()  # update_delta=newnow - now)
        print(f"servertime: {ex.servertime}")
        now = newnow
        print(f"now: {now}")

    asyncio.run(run_exchg())

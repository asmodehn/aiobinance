import dataclasses
import functools
import re
from datetime import datetime, timezone
from typing import List

from aiobinance.api.market import Market
from aiobinance.api.model.filters import Filter
from aiobinance.api.model.market_info import MarketInfo
from aiobinance.api.pure.exchange import Exchange as ExchangeInfo
from aiobinance.api.pure.exchange import RateLimit
from aiobinance.api.rawapi import Binance

# converting camel case (API) to snake case (aiobinance)
camel_snake = re.compile(r"(?<!^)(?=[A-Z])")


class Exchange:
    """ A class to simplify interacting with binance exchange through the REST API."""

    api: Binance

    def __init__(
        self,
        api: Binance,
        servertime: datetime,
        rate_limits: List[RateLimit],
        exchange_filters: List[Filter],
        symbols: List[MarketInfo],
        async_loop=None,
        test=True,
    ):
        # if an async loop is passed, call is run in the background to update data out-of-band
        # currently polling in the background, later TODO : websockets

        self.api = api
        self.test = (
            test  # wether we will be able to actually do anything with this exchange
        )
        self.servertime = servertime
        self.rate_limits = rate_limits
        self.exchange_filters = exchange_filters
        self.market = {
            s.symbol: Market(api=self.api, info=s, async_loop=async_loop, test=test)
            for s in symbols
        }

    # TODO : implement rate limiting somehow...


def retrieve_exchange(api: Binance, test: bool = True) -> Exchange:

    res = api.call_api(command="exchangeInfo")

    if res.is_ok():
        res = res.value
    else:
        # TODO : handle API error properly
        raise RuntimeError(res.value)

    # timezone mess
    if res["timezone"] == "UTC":
        tz = timezone.utc
    else:
        raise RuntimeError("Unknown timezone !")

    # Binance translation is only a matter of binance json -> python data structure && avoid data duplication.
    # We do not want to change the semantics of the exchange exposed models here.
    exchange = ExchangeInfo(
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
                        **{camel_snake.sub("_", fk).lower(): fv for fk, fv in f.items()}
                    )
                    for f in s["filters"]
                ],
                permissions=s["permissions"],
            )
            for s in res["symbols"]
        ],
    )

    return Exchange(
        api=api,
        servertime=exchange.servertime,
        rate_limits=exchange.rate_limits,
        exchange_filters=exchange.exchange_filters,
        symbols=exchange.symbols,
        test=test,
    )

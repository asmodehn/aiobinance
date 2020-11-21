import dataclasses
import functools
from datetime import datetime, timezone
from typing import List

from aiobinance.api.market import Market
from aiobinance.api.rawapi import Binance
from aiobinance.model.exchange import Exchange as ExchangeInfo
from aiobinance.model.exchange import Filter, RateLimit, Symbol


class Exchange:
    """ A class to simplify interacting with binance exchange through the REST API."""

    api: Binance

    def __init__(
        self,
        api: Binance,
        servertime: datetime,
        rate_limits: List[RateLimit],
        exchange_filters: List[Filter],
        symbols: List[Symbol],
        async_loop=None,
    ):
        # if an async loop is passed, call is run in the background to update data out-of-band
        # currently polling in the background, later TODO : websockets

        self.api = api
        self.servertime = servertime
        self.rate_limits = rate_limits
        self.exchange_filters = exchange_filters
        self.market = {
            s.symbol: Market(
                api=self.api,
                symbol=s.symbol,
                status=s.status,
                base_asset=s.base_asset,
                base_asset_precision=s.base_asset_precision,
                quote_asset=s.quote_asset,
                quote_precision=s.quote_precision,
                quote_asset_precision=s.quote_asset_precision,
                base_commission_precision=s.base_commission_precision,
                quote_commission_precision=s.quote_commission_precision,
                order_types=s.order_types,
                iceberg_allowed=s.iceberg_allowed,
                oco_allowed=s.oco_allowed,
                is_spot_trading_allowed=s.is_spot_trading_allowed,
                is_margin_trading_allowed=s.is_margin_trading_allowed,
                quote_order_qty_market_allowed=s.quote_order_qty_market_allowed,
                filters=s.filters,
                permissions=s.permissions,
                async_loop=async_loop,
            )
            for s in symbols
        }

    # TODO : implement rate limiting somehow...


def retrieve_exchange(api: Binance) -> Exchange:

    res = api.call_api(command="exchangeInfo")

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
            Symbol(
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
                    Filter(
                        filter_type=f["filterType"],
                        min_price=f.get("minPrice"),
                        max_price=f.get("maxPrice"),
                        tick_size=f.get("tickSize"),
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
    )

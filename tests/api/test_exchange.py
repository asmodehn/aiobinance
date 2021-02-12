from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from aiobinance.api.exchange import Exchange
from aiobinance.api.model.exchange_info import RateLimit
from aiobinance.api.model.filters import Filter
from aiobinance.api.rawapi import Binance


@pytest.mark.asyncio
@pytest.mark.vcr
async def test_exchange_from_binance():
    """ get binance exchange info"""

    api = Binance()  # we don't need private requests here

    exchange = Exchange(
        api=api, test=True
    )  # test or not doesnt really matter here, we only read.

    assert isinstance(exchange, Exchange)
    assert exchange.info is None
    assert exchange.api is api
    assert exchange.test is True

    await exchange()  # mandatory to retrieve actual data !

    assert exchange.info is not None  # info has been updated !
    assert exchange.api is api
    assert exchange.test is True

    assert (
        exchange.info.exchange_filters == []
    )  # TODO : try to get better sample for testing this...
    assert len(exchange.info.rate_limits) == 3

    # Also validating subtypes...

    assert (
        RateLimit(
            rate_limit_type="REQUEST_WEIGHT",
            interval="MINUTE",
            interval_num=1,
            limit=1200,
        )
        in exchange.info.rate_limits
    )
    assert (
        RateLimit(
            rate_limit_type="ORDERS", interval="SECOND", interval_num=10, limit=100
        )
        in exchange.info.rate_limits
    )
    assert (
        RateLimit(
            rate_limit_type="ORDERS", interval="DAY", interval_num=1, limit=200_000
        )
        in exchange.info.rate_limits
    )

    assert exchange.servertime == datetime(
        year=2020,
        month=11,
        day=21,
        hour=9,
        minute=59,
        second=49,
        microsecond=550000,
        tzinfo=timezone.utc,
    )

    # Validating only one market...
    ethbtc_market = exchange.markets["ETHBTC"]
    assert ethbtc_market.info.base_asset == "ETH"
    assert ethbtc_market.info.base_asset_precision == 8
    assert ethbtc_market.info.base_commission_precision == 8
    assert ethbtc_market.info.filters == [
        Filter.factory(
            filter_type="PRICE_FILTER",
            min_price=Decimal("0.00000100"),
            max_price=Decimal("100000.00000000"),
            tick_size=Decimal("0.00000100"),
        ),
        Filter.factory(
            filter_type="PERCENT_PRICE",
            multiplier_up=Decimal("5"),
            multiplier_down=Decimal("0.2"),
            avg_price_mins=5,
        ),
        Filter.factory(
            filter_type="LOT_SIZE",
            min_qty=Decimal("0.00100000"),
            max_qty=Decimal("100000.00000000"),
            step_size=Decimal("0.00100000"),
        ),
        Filter.factory(
            filter_type="MIN_NOTIONAL",
            min_notional=Decimal("0.00010000"),
            apply_to_market=True,
            avg_price_mins=5,
        ),
        Filter.factory(filter_type="ICEBERG_PARTS", limit=10),
        Filter.factory(
            filter_type="MARKET_LOT_SIZE",
            min_qty=Decimal("0E-8"),
            max_qty=Decimal("4961.68384167"),
            step_size=Decimal("0E-8"),
        ),
        Filter.factory(filter_type="MAX_NUM_ALGO_ORDERS", max_num_algo_orders=5),
        Filter.factory(filter_type="MAX_NUM_ORDERS", max_num_orders=200),
    ]
    assert ethbtc_market.info.iceberg_allowed is True
    assert ethbtc_market.info.is_margin_trading_allowed is True
    assert ethbtc_market.info.is_spot_trading_allowed is True
    assert ethbtc_market.info.oco_allowed is True
    assert ethbtc_market.info.order_types == [
        "LIMIT",
        "LIMIT_MAKER",
        "MARKET",
        "STOP_LOSS_LIMIT",
        "TAKE_PROFIT_LIMIT",
    ]
    assert ethbtc_market.info.permissions == ["SPOT", "MARGIN"]
    assert ethbtc_market.info.quote_asset == "BTC"
    assert ethbtc_market.info.quote_asset_precision == 8
    assert ethbtc_market.info.quote_commission_precision == 8
    assert ethbtc_market.info.quote_order_qty_market_allowed is True
    assert ethbtc_market.info.quote_precision == 8
    assert ethbtc_market.info.status == "TRADING"
    assert ethbtc_market.info.symbol == "ETHBTC"


if __name__ == "__main__":
    pytest.main(["-s", __file__, "--block-network"])
    # record run
    # pytest.main(['-s', __file__, '--with-keyfile', '--record-mode=new_episodes'])

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

import aiobinance.binance
from aiobinance.model import TradeFrame
from aiobinance.model.account import Account
from aiobinance.model.exchange import Exchange, Filter, RateLimit, Symbol
from aiobinance.model.ohlcv import OHLCV, Candle
from aiobinance.model.ticker import Ticker
from aiobinance.model.trade import Trade


@pytest.mark.vcr
def test_exchange_from_binance():
    """ get binance exchange info"""

    exchange = aiobinance.binance.exchange_from_binance()

    assert isinstance(exchange, Exchange)

    assert (
        exchange.exchange_filters == []
    )  # TODO : try to get better sample for testing this...
    assert len(exchange.rate_limits) == 3

    # Also validating subtypes...

    assert (
        RateLimit(
            rate_limit_type="REQUEST_WEIGHT",
            interval="MINUTE",
            interval_num=1,
            limit=1200,
        )
        in exchange.rate_limits
    )
    assert (
        RateLimit(
            rate_limit_type="ORDERS", interval="SECOND", interval_num=10, limit=100
        )
        in exchange.rate_limits
    )
    assert (
        RateLimit(
            rate_limit_type="ORDERS", interval="DAY", interval_num=1, limit=200_000
        )
        in exchange.rate_limits
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

    # Validating only one symbol...
    assert (
        Symbol(
            base_asset="ETH",
            base_asset_precision=8,
            base_commission_precision=8,
            filters=[
                Filter(
                    filter_type="PRICE_FILTER",
                    min_price=Decimal("0.00000100"),
                    max_price=Decimal("100000.00000000"),
                    tick_size=Decimal("0.00000100"),
                ),
                Filter(filter_type="PERCENT_PRICE"),
                Filter(filter_type="LOT_SIZE"),
                Filter(filter_type="MIN_NOTIONAL"),
                Filter(filter_type="ICEBERG_PARTS"),
                Filter(filter_type="MARKET_LOT_SIZE"),
                Filter(filter_type="MAX_NUM_ALGO_ORDERS"),
                Filter(filter_type="MAX_NUM_ORDERS"),
            ],
            iceberg_allowed=True,
            is_margin_trading_allowed=True,
            is_spot_trading_allowed=True,
            oco_allowed=True,
            order_types=[
                "LIMIT",
                "LIMIT_MAKER",
                "MARKET",
                "STOP_LOSS_LIMIT",
                "TAKE_PROFIT_LIMIT",
            ],
            permissions=["SPOT", "MARGIN"],
            quote_asset="BTC",
            quote_asset_precision=8,
            quote_commission_precision=8,
            quote_order_qty_market_allowed=True,
            quote_precision=8,
            status="TRADING",
            symbol="ETHBTC",
        )
        in exchange.symbols
    )


@pytest.mark.vcr(
    filter_headers=["X-MBX-APIKEY"], filter_query_parameters=["timestamp", "signature"]
)
def test_balance_from_binance(keyfile):
    """ get binance balances"""

    account = aiobinance.binance.balance_from_binance(credentials=keyfile)

    assert isinstance(account, Account)
    assert account.accountType == "SPOT"
    assert len(account.balances) == 337  # TMP might change...
    assert account.buyerCommission == 0
    assert account.canDeposit is True
    assert account.canTrade is True
    assert account.canWithdraw is True
    assert account.makerCommission == 10
    assert "SPOT" in account.permissions
    assert account.sellerCommission == 0
    assert account.takerCommission == 10
    assert hasattr(account, "updateTime")


@pytest.mark.vcr(
    filter_headers=["X-MBX-APIKEY"], filter_query_parameters=["timestamp", "signature"]
)
def test_trades_from_binance(keyfile):
    """ get binance balances"""

    start_time = datetime.fromtimestamp(1598524340551 / 1000, tz=timezone.utc)
    end_time = start_time + timedelta(days=1)
    trades = aiobinance.binance.trades_from_binance(
        "COTIBNB", start_time=start_time, end_time=end_time, credentials=keyfile
    )

    assert isinstance(trades, TradeFrame)

    assert len(trades) == 17
    for t in trades:
        assert isinstance(t, Trade)

    first = trades[0]
    assert start_time < first.time < end_time
    assert first.time == datetime(
        year=2020,
        month=8,
        day=27,
        hour=10,
        minute=57,
        second=44,
        microsecond=478000,
        tzinfo=timezone.utc,
    )
    assert first.symbol == "COTIBNB"
    assert first.id == 299229
    assert first.order_id == 18443055
    assert first.commission == Decimal("0.00066035")
    assert first.commission_asset == "BNB"
    assert first.is_best_match is True
    assert first.is_buyer is False
    assert first.is_maker is True
    assert first.order_list_id == -1  # TODO : should probably be None internally ?
    assert first.price == Decimal("0.00326100")
    assert first.qty == Decimal("300.000000000")
    assert first.quote_qty == Decimal("0.97830000")


@pytest.mark.vcr
def test_price_from_binance():
    """ get binance price"""

    start_time = datetime.fromtimestamp(1598524340551 / 1000, tz=timezone.utc)
    end_time = start_time + timedelta(days=1)
    ohlcv = aiobinance.binance.price_from_binance(
        "COTIBNB", start_time=start_time, end_time=end_time, interval="3m"
    )

    assert isinstance(ohlcv, OHLCV)

    assert len(ohlcv) == 480
    for c in ohlcv:
        assert isinstance(c, Candle)

    first = ohlcv[0]
    assert first.open_time == datetime(
        year=2020, month=8, day=27, hour=10, minute=33, tzinfo=timezone.utc
    )
    assert first.open == Decimal("0.00320100")
    assert first.high == Decimal("0.00322600")
    assert first.low == Decimal("0.00320100")
    assert first.close == Decimal("0.00322600")
    assert first.volume == Decimal("7705.00000000")
    assert first.close_time == datetime(
        year=2020,
        month=8,
        day=27,
        hour=10,
        minute=35,
        second=59,
        microsecond=999000,
        tzinfo=timezone.utc,
    )
    assert first.qav == Decimal("24.66804700")
    assert first.num_trades == 5
    assert first.taker_base_vol == Decimal("176.00000000")
    assert first.taker_quote_vol == Decimal("0.56771800")
    assert first.is_best_match == 0  # ??


@pytest.mark.vcr
def test_ticker_from_binance():
    """ get binance ticker"""
    ticker = aiobinance.binance.ticker24_from_binance("COTIBNB")

    assert isinstance(ticker, Ticker)

    assert ticker.ask_price == Decimal("0.00120300")
    assert ticker.bid_price == Decimal("0.00119900")
    assert ticker.close_time == datetime(
        year=2020,
        month=11,
        day=9,
        hour=17,
        minute=17,
        microsecond=79000,
        tzinfo=timezone.utc,
    )
    assert ticker.count == 2810
    assert ticker.first_id == 454001
    assert ticker.high_price == Decimal("0.00126300")
    assert ticker.last_id == 456810
    assert ticker.last_price == Decimal("0.00120200")
    assert ticker.last_qty == Decimal("3004.00000000")
    assert ticker.low_price == Decimal("0.00114700")
    assert ticker.open_price == Decimal("0.00126200")
    assert ticker.open_time == datetime(
        year=2020,
        month=11,
        day=8,
        hour=17,
        minute=17,
        microsecond=79000,
        tzinfo=timezone.utc,
    )
    assert ticker.prev_close_price == Decimal("0.00125800")
    assert ticker.price_change == Decimal("-0.000060000")
    assert ticker.price_change_percent == Decimal("-4.754")
    assert ticker.quote_volume == Decimal("3631.82546700")
    assert ticker.symbol == "COTIBNB"
    assert ticker.volume == Decimal("3013981.00000000")
    assert ticker.weighted_avg_price == Decimal("0.00120499")


if __name__ == "__main__":
    pytest.main(["-s", __file__, "--block-network"])
    # record run
    # pytest.main(['-s', __file__, '--with-keyfile', '--record-mode=new_episodes'])

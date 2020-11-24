from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from result import Result

import aiobinance.binance
from aiobinance.api.account import Account
from aiobinance.api.exchange import Exchange
from aiobinance.api.market import Market
from aiobinance.model import TradeFrame
from aiobinance.model.exchange import Filter, RateLimit, Symbol
from aiobinance.model.ohlcv import OHLCV, Candle
from aiobinance.model.order import LimitOrder, MarketOrder, OrderFill
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

    # Validating only one market...
    ethbtc_market = exchange.market["ETHBTC"]
    assert ethbtc_market.base_asset == "ETH"
    assert ethbtc_market.base_asset_precision == 8
    assert ethbtc_market.base_commission_precision == 8
    assert ethbtc_market.filters == [
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
    ]
    assert ethbtc_market.iceberg_allowed is True
    assert ethbtc_market.is_margin_trading_allowed is True
    assert ethbtc_market.is_spot_trading_allowed is True
    assert ethbtc_market.oco_allowed is True
    assert ethbtc_market.order_types == [
        "LIMIT",
        "LIMIT_MAKER",
        "MARKET",
        "STOP_LOSS_LIMIT",
        "TAKE_PROFIT_LIMIT",
    ]
    assert ethbtc_market.permissions == ["SPOT", "MARGIN"]
    assert ethbtc_market.quote_asset == "BTC"
    assert ethbtc_market.quote_asset_precision == 8
    assert ethbtc_market.quote_commission_precision == 8
    assert ethbtc_market.quote_order_qty_market_allowed is True
    assert ethbtc_market.quote_precision == 8
    assert ethbtc_market.status == "TRADING"
    assert ethbtc_market.symbol == "ETHBTC"


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


@pytest.mark.vcr(
    filter_headers=["X-MBX-APIKEY"], filter_query_parameters=["timestamp", "signature"]
)
def test_limitorder_test_to_binance(keyfile):
    """ send orders to binance """

    res_order = aiobinance.binance.limitorder_to_binance(
        symbol="COTIBNB",
        side="BUY",
        quantity=Decimal("300"),
        price=Decimal("0.0015"),
        credentials=keyfile,
    )

    assert res_order and isinstance(res_order, Result)
    assert isinstance(res_order.value, LimitOrder)
    assert res_order.value.clientOrderId == ""
    assert res_order.value.cummulativeQuoteQty.is_zero()
    assert res_order.value.executedQty.is_zero()
    assert res_order.value.fills == []
    assert res_order.value.icebergQty is None
    assert res_order.value.order_id == -1
    assert res_order.value.order_list_id == -1
    assert res_order.value.origQty == Decimal("300")
    assert res_order.value.price == Decimal("0.0015")
    assert res_order.value.side == "BUY"
    assert res_order.value.status == "TEST"
    assert res_order.value.symbol == "COTIBNB"
    assert res_order.value.timeInForce == "GTC"
    assert res_order.value.type == "LIMIT"

    # transac time has a dynamic value because it does not depend on recorded traffic !
    # This is measuring with second precision a time in ms
    assert res_order.value.transactTime // 1000 == int(
        datetime.now(tz=timezone.utc).timestamp()
    )


@pytest.mark.vcr(
    filter_headers=["X-MBX-APIKEY"], filter_query_parameters=["timestamp", "signature"]
)
def test_limitorder_to_binance(keyfile):
    """ send orders to binance """

    res_order = aiobinance.binance.limitorder_to_binance(
        symbol="COTIBNB",
        side="BUY",
        quantity=Decimal("300"),
        price=Decimal("0.0015"),
        credentials=keyfile,
        test=False,
    )

    assert res_order and isinstance(res_order, Result)
    assert isinstance(res_order.value, LimitOrder)
    assert res_order.value.clientOrderId == "UIwsOoNnCNJlxHFCwtikDI"
    assert res_order.value.cummulativeQuoteQty.is_zero()
    assert res_order.value.executedQty.is_zero()
    assert res_order.value.fills == []
    assert res_order.value.icebergQty is None
    assert res_order.value.order_id == 31085682
    assert res_order.value.order_list_id == -1
    assert res_order.value.origQty == Decimal("300")
    assert res_order.value.price == Decimal("0.0015")
    assert res_order.value.side == "BUY"
    assert res_order.value.status == "NEW"
    assert res_order.value.symbol == "COTIBNB"
    assert res_order.value.timeInForce == "GTC"
    assert res_order.value.transactTime == 1605967825942
    assert res_order.value.type == "LIMIT"


@pytest.mark.vcr(
    filter_headers=["X-MBX-APIKEY"], filter_query_parameters=["timestamp", "signature"]
)
def test_marketorder_test_to_binance(keyfile):
    """ send orders to binance """

    res_order = aiobinance.binance.marketorder_to_binance(
        symbol="COTIBNB", side="BUY", quantity=Decimal("300"), credentials=keyfile
    )

    assert res_order and isinstance(res_order, Result)
    assert isinstance(res_order.value, MarketOrder)
    assert res_order.value.clientOrderId == ""
    assert res_order.value.cummulativeQuoteQty.is_zero()
    assert res_order.value.executedQty.is_zero()
    assert res_order.value.fills == []
    assert res_order.value.order_id == -1
    assert res_order.value.order_list_id == -1
    assert res_order.value.origQty == Decimal("300")
    assert res_order.value.quoteOrderQty is None
    assert res_order.value.side == "BUY"
    assert res_order.value.status == "TEST"
    assert res_order.value.symbol == "COTIBNB"
    assert res_order.value.type == "MARKET"

    # transac time has a dynamic value because it does not depend on recorded traffic !
    # This is measuring with second precision a time in ms
    assert res_order.value.transactTime // 1000 == int(
        datetime.now(tz=timezone.utc).timestamp()
    )


@pytest.mark.vcr(
    filter_headers=["X-MBX-APIKEY"], filter_query_parameters=["timestamp", "signature"]
)
def test_marketorder_to_binance(keyfile):
    """ send orders to binance """

    res_order = aiobinance.binance.marketorder_to_binance(
        symbol="COTIBNB",
        side="BUY",
        quantity=Decimal("300"),
        credentials=keyfile,
        test=False,
    )

    assert res_order and isinstance(res_order, Result)
    assert isinstance(res_order.value, MarketOrder)
    assert res_order.value.clientOrderId == "DfbcHz3JSKjoIUUUGB8lEj"
    assert res_order.value.cummulativeQuoteQty == Decimal("0.45300000")
    assert res_order.value.executedQty == Decimal("300.00000000")
    assert res_order.value.fills == [
        OrderFill(
            price=Decimal("0.00151000"),
            qty=Decimal("300.00000000"),
            commission=Decimal("0.00033873"),
            commissionAsset="BNB",
            tradeId=481909,
        )
    ]
    assert res_order.value.order_id == 31085683
    assert res_order.value.order_list_id == -1
    assert res_order.value.origQty == Decimal("300")
    assert res_order.value.quoteOrderQty is None
    assert res_order.value.side == "BUY"
    assert res_order.value.status == "FILLED"
    assert res_order.value.symbol == "COTIBNB"
    assert res_order.value.transactTime == 1605967826275
    assert res_order.value.type == "MARKET"


if __name__ == "__main__":
    pytest.main(["-s", __file__, "--block-network"])
    # record run
    # pytest.main(['-s', __file__, '--with-keyfile', '--record-mode=new_episodes'])

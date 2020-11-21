from datetime import datetime, timezone
from typing import Optional

import pandas as pd

from aiobinance.api import BinanceRaw
from aiobinance.config import Credentials, load_api_keyfile
from aiobinance.model.account import Account
from aiobinance.model.exchange import Exchange, Filter, RateLimit, Symbol
from aiobinance.model.ohlcv import OHLCV, Candle
from aiobinance.model.ticker import Ticker
from aiobinance.model.trade import Trade, TradeFrame


def exchange_from_binance() -> Exchange:
    api = BinanceRaw(API_KEY="", API_SECRET="")  # we dont need private requests here

    res = api.call_api(command="exchangeInfo")

    # timezone mess
    if res["timezone"] == "UTC":
        tz = timezone.utc
    else:
        raise RuntimeError("Unknown timezone !")

    # Binance translation is only a matter of binance json -> python data structure && avoid data duplication.
    # We do not want to change the semantics of the exchange exposed models here.
    exchange = Exchange(
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

    return exchange


def balance_from_binance(*, credentials: Credentials = load_api_keyfile()) -> Account:
    api = BinanceRaw(
        API_KEY=credentials.key, API_SECRET=credentials.secret
    )  # we need private requests here !

    res = api.call_api(command="account")

    # Binance translation is only a matter of binance json -> python data structure && avoid data duplication.
    # We do not want to change the semantics of the exchange exposed models here.
    account = Account(
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

    return account


def trades_from_binance(
    symbol: str,
    *,
    start_time: datetime,
    end_time: datetime,
    credentials: Credentials = load_api_keyfile()
) -> TradeFrame:
    api = BinanceRaw(
        API_KEY=credentials.key, API_SECRET=credentials.secret
    )  # we need private requests here !

    # to make sure the timezone is set at this stage (otherwise timestamps will be ambiguous)
    assert start_time.tzinfo is not None
    assert end_time.tzinfo is not None

    start_timestamp = int(start_time.timestamp() * 1000)
    end_timestamp = int(end_time.timestamp() * 1000)

    res = api.call_api(
        command="myTrades",
        symbol=symbol,
        startTime=start_timestamp,
        endTime=end_timestamp,
        limit=1000,
    )

    # Binance translation is only a matter of binance json -> python data structure && avoid data duplication.
    # We do not want to change the semantics of the exchange exposed models here.
    trades = [
        Trade(
            time=r["time"],
            symbol=r["symbol"],
            id=r["id"],
            order_id=r["orderId"],
            order_list_id=r["orderListId"],
            price=r["price"],
            qty=r["qty"],
            quote_qty=r["quoteQty"],
            commission=r["commission"],
            commission_asset=r["commissionAsset"],
            is_buyer=r["isBuyer"],
            is_maker=r["isMaker"],
            is_best_match=r["isBestMatch"],
        )
        for r in res
    ]

    # We aggregate all formatted trades into a TradeFrame
    return TradeFrame(*trades)


def price_from_binance(
    symbol: str, *, start_time: datetime, end_time: datetime, interval=None
) -> OHLCV:
    api = BinanceRaw(API_KEY="", API_SECRET="")  # we dont need private requests here
    # Ref : https://binance-docs.github.io/apidocs/spot/en/#kline-candlestick-data

    # to make sure the timezone is set at this stage (otherwise timestamps will be ambiguous)
    assert start_time.tzinfo is not None
    assert end_time.tzinfo is not None

    start_timestamp = int(start_time.timestamp() * 1000)
    end_timestamp = int(end_time.timestamp() * 1000)
    interval = (
        interval
        if interval is not None
        else BinanceRaw.interval(start_timestamp, end_timestamp)
    )

    res = api.call_api(
        command="klines",
        symbol=symbol,
        interval=interval,
        startTime=start_timestamp,
        endTime=end_timestamp,
        limit=1000,
    )

    # Binance translation is only a matter of binance json -> python data structure && avoid data duplication.
    # We do not want to change the semantics of the exchange exposed models here.
    candles = [
        Candle(
            open_time=r[0],
            open=r[1],
            high=r[2],
            low=r[3],
            close=r[4],
            volume=r[5],
            close_time=r[6],
            qav=r[7],
            num_trades=r[8],
            taker_base_vol=r[9],
            taker_quote_vol=r[10],
            is_best_match=r[11],
        )
        for r in res
    ]

    return OHLCV(*candles)


def ticker24_from_binance(
    symbol: str,
):
    api = BinanceRaw(API_KEY="", API_SECRET="")  # we dont need private requests here
    res = api.call_api(
        command="ticker24hr",
        symbol=symbol,
    )

    # Binance translation is only a matter of binance json -> python data structure && avoid data duplication.
    # We do not want to change the semantics of the exchange exposed models here.
    return Ticker(
        symbol=res["symbol"],
        price_change=res["priceChange"],
        price_change_percent=res["priceChangePercent"],
        weighted_avg_price=res["weightedAvgPrice"],
        prev_close_price=res["prevClosePrice"],
        last_price=res["lastPrice"],
        last_qty=res["lastQty"],
        bid_price=res["bidPrice"],
        ask_price=res["askPrice"],
        open_price=res["openPrice"],
        high_price=res["highPrice"],
        low_price=res["lowPrice"],
        volume=res["volume"],
        quote_volume=res["quoteVolume"],
        open_time=res["openTime"],
        close_time=res["closeTime"],
        first_id=res["firstId"],
        last_id=res["lastId"],
        count=res["count"],
    )


if __name__ == "__main__":
    # TODO : whats the most useful way to run this module ? doctest ? manual repl test ?
    print(balance_from_binance())
    print(
        trades_from_binance(
            "COTIBNB",
            start_time=datetime.fromtimestamp(1598524340551 / 1000),
            end_time=datetime.fromtimestamp(1598893442120 / 1000),
        )
    )
    print(
        price_from_binance(
            "COTIBNB",
            start_time=datetime.fromtimestamp(1598524340551 / 1000),
            end_time=datetime.fromtimestamp(1598893442120 / 1000),
        )
    )

from datetime import datetime
from typing import Optional

import pandas as pd

from aiobinance.api import BinanceRaw
from aiobinance.config import Credentials, load_api_keyfile
from aiobinance.model.account import Account
from aiobinance.model.ohlcv import OHLCV, Candle
from aiobinance.model.trade import Trade, TradeFrame


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
    start_time: int,
    end_time: int,
    credentials: Credentials = load_api_keyfile()
) -> TradeFrame:
    api = BinanceRaw(
        API_KEY=credentials.key, API_SECRET=credentials.secret
    )  # we need private requests here !

    res = api.call_api(
        command="myTrades",
        symbol=symbol,
        startTime=start_time,
        endTime=end_time,
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


def price_from_binance(symbol: str, *, start_time: int, end_time: int) -> OHLCV:
    api = BinanceRaw(API_KEY="", API_SECRET="")  # we dont need private requests here
    # Ref : https://binance-docs.github.io/apidocs/spot/en/#kline-candlestick-data

    interval = BinanceRaw.interval(start_time, end_time)

    res = api.call_api(
        command="klines",
        symbol=symbol,
        interval=interval,
        startTime=start_time,
        endTime=end_time,
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


if __name__ == "__main__":
    # TODO : whats the most useful way to run this module ? doctest ? manual repl test ?
    print(balance_from_binance())
    print(
        trades_from_binance("COTIBNB", start_time=1598524340551, end_time=1598893442120)
    )
    print(
        price_from_binance("COTIBNB", start_time=1598524340551, end_time=1598893442120)
    )

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

import pandas as pd

from aiobinance.api import BinanceRaw
from aiobinance.api.exchange import Exchange, retrieve_exchange
from aiobinance.api.market import Market
from aiobinance.config import Credentials, load_api_keyfile
from aiobinance.model.account import Account
from aiobinance.model.exchange import Filter, RateLimit, Symbol
from aiobinance.model.ohlcv import OHLCV, Candle
from aiobinance.model.order import LimitOrder, MarketOrder, Order
from aiobinance.model.ticker import Ticker
from aiobinance.model.trade import Trade, TradeFrame


def exchange_from_binance() -> Exchange:
    api = BinanceRaw(API_KEY="", API_SECRET="")  # we don't need private requests here

    exchange = retrieve_exchange(api=api)

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

    exchange = retrieve_exchange(api=api)

    trades = exchange.market[symbol].trades(start_time=start_time, end_time=end_time)
    return trades


def price_from_binance(
    symbol: str, *, start_time: datetime, end_time: datetime, interval=None
) -> OHLCV:
    api = BinanceRaw(API_KEY="", API_SECRET="")  # we dont need private requests here
    # Ref : https://binance-docs.github.io/apidocs/spot/en/#kline-candlestick-data

    exchange = retrieve_exchange(api=api)

    price = exchange.market[symbol].price(
        start_time=start_time, end_time=end_time, interval=interval
    )
    return price


def ticker24_from_binance(
    symbol: str,
):
    api = BinanceRaw(API_KEY="", API_SECRET="")  # we dont need private requests here

    exchange = retrieve_exchange(api=api)

    ticker = exchange.market[symbol].ticker24()
    return ticker


def limitorder_to_binance(
    symbol: str,
    side: str,
    price: Decimal,
    quantity: Decimal,
    *,
    credentials: Credentials = load_api_keyfile()
) -> LimitOrder:
    api = BinanceRaw(
        API_KEY=credentials.key, API_SECRET=credentials.secret
    )  # we need private requests here !

    exchange = retrieve_exchange(api=api)

    order = exchange.market[symbol].limit_order(
        side=side, price=price, quantity=quantity
    )
    return order


def marketorder_to_binance(
    symbol: str,
    side: str,
    quantity: Decimal,
    *,
    credentials: Credentials = load_api_keyfile()
) -> TradeFrame:
    api = BinanceRaw(
        API_KEY=credentials.key, API_SECRET=credentials.secret
    )  # we need private requests here !

    exchange = retrieve_exchange(api=api)

    order = exchange.market[symbol].market_order(side=side, quantity=quantity)
    return order


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

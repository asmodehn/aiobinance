from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

import pandas as pd
from result import Result

from aiobinance.api import BinanceRaw
from aiobinance.api.account import retrieve_account
from aiobinance.api.exchange import Exchange, retrieve_exchange
from aiobinance.api.market import Market
from aiobinance.api.pure.account import Account
from aiobinance.api.pure.order import LimitOrder, MarketOrder, Order, OrderSide
from aiobinance.config import Credentials, load_api_keyfile
from aiobinance.model.ohlcv import OHLCV, Candle
from aiobinance.model.trade import Trade, TradeFrame

# TODO : note this module will eventually disappear... code will be moved to various modules around...


def exchange_from_binance() -> Exchange:
    api = BinanceRaw()  # we don't need private requests here

    exchange = retrieve_exchange(api=api)

    return exchange


def balance_from_binance(*, credentials: Credentials = load_api_keyfile()) -> Account:
    api = BinanceRaw(credentials=credentials)  # we need private requests here !

    account = retrieve_account(api=api)

    return account


def trades_from_binance(
    symbol: str,
    *,
    start_time: datetime,
    end_time: datetime,
    credentials: Credentials = load_api_keyfile()
) -> TradeFrame:
    api = BinanceRaw(credentials=credentials)  # we need private requests here !

    exchange = retrieve_exchange(api=api)

    trades = exchange.market[symbol].trades(start_time=start_time, end_time=end_time)
    return trades


def price_from_binance(
    symbol: str, *, start_time: datetime, end_time: datetime, interval=None
) -> OHLCV:
    api = BinanceRaw(credentials=None)  # we dont need private requests here
    # Ref : https://binance-docs.github.io/apidocs/spot/en/#kline-candlestick-data

    exchange = retrieve_exchange(api=api)

    price = exchange.market[symbol].price(
        start_time=start_time, end_time=end_time, interval=interval
    )
    return price


def ticker24_from_binance(
    symbol: str,
):
    api = BinanceRaw(credentials=None)  # we dont need private requests here

    exchange = retrieve_exchange(api=api)

    ticker = exchange.market[symbol].ticker24()
    return ticker


def limitorder_to_binance(
    symbol: str,
    side: OrderSide,
    price: Decimal,
    quantity: Decimal,
    *,
    credentials: Credentials = load_api_keyfile(),
    test: bool = True
) -> Result[LimitOrder, None]:  # TODO : better error ?
    api = BinanceRaw(
        credentials=Credentials(key=credentials.key, secret=credentials.secret)
    )  # we need private requests here !

    exchange = retrieve_exchange(api=api)

    order = exchange.market[symbol].limit_order(
        side=side, price=price, quantity=quantity, test=test
    )
    return order


def marketorder_to_binance(
    symbol: str,
    side: OrderSide,
    quantity: Decimal,
    *,
    credentials: Credentials = load_api_keyfile(),
    test: bool = True
) -> Result[TradeFrame, None]:  # TODO : better error ?
    api = BinanceRaw(
        credentials=Credentials(key=credentials.key, secret=credentials.secret)
    )  # we need private requests here !

    exchange = retrieve_exchange(api=api)

    order = exchange.market[symbol].market_order(
        side=side, quantity=quantity, test=test
    )
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

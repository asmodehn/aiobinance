import asyncio
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

import pandas as pd
from result import Result

from aiobinance.api import BinanceRaw
from aiobinance.api.account import Account
from aiobinance.api.exchange import Exchange
from aiobinance.api.market import Market
from aiobinance.api.model.order import LimitOrder, MarketOrder, Order, OrderSide
from aiobinance.api.pure.ohlcviewbase import OHLCFrame
from aiobinance.api.pure.tradesviewbase import TradeFrame
from aiobinance.config import Credentials, load_api_keyfile

# TODO : note this module will eventually disappear... code will be moved to various modules around...


def ticker24_from_binance(
    symbol: str,
):
    import asyncio

    api = BinanceRaw(credentials=None)  # we dont need private requests here

    exchange = Exchange(api=api)

    # because we are moving to an async interface...
    asyncio.run(exchange())

    ticker = exchange.markets[symbol].ticker24()
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

    exchange = Exchange(api=api, test=test)

    asyncio.run(exchange())

    order = exchange.markets[symbol].limit_order(
        side=side, price=price, quantity=quantity
    )
    return order


if __name__ == "__main__":
    # TODO : whats the most useful way to run this module ? doctest ? manual repl test ?
    pass

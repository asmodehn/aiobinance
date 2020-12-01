from __future__ import annotations

import asyncio
import decimal
from asyncio import AbstractEventLoop
from decimal import Decimal
from typing import Optional

from aiobinance.api.account import Account
from aiobinance.api.exchange import retrieve_exchange
from aiobinance.api.market import Market
from aiobinance.api.model.order import LimitOrder
from aiobinance.api.rawapi import Binance
from aiobinance.bot.safecounter import SafeCounter


class TraderException(Exception):
    pass


class Trader:
    def __init__(self, account: Account, market: Market):
        self.account = account
        self.market = market

        # getting ticker only once (careful with side-effects...)
        tkr = self.market.ticker24()

        # currently only using this as a safe counter...
        self.safe_counter = SafeCounter.from_ticker(mkt=market, tkr=tkr)

        self._loop = None
        self._running = None

    # TODO :retrieve cost of asset in past trades, to determine cost...
    # TODO : some forcasting to determine opportunity...
    # TODO : then do some time-based arbitrage... hodl or fomo ?

    def sell(
        self, amount: Decimal, total_expected: Optional[Decimal] = None
    ) -> LimitOrder:

        passed_order = asyncio.run(
            self.safe_counter.sell(amount=amount, expected_gain=total_expected)
        )
        if passed_order.is_ok():
            return passed_order.ok()
        else:
            raise TraderException(passed_order.err())

    def buy(
        self, amount: Decimal, total_expected: Optional[Decimal] = None
    ) -> LimitOrder:
        passed_order = asyncio.run(
            self.safe_counter.buy(amount=amount, expected_cost=total_expected)
        )
        if passed_order.is_ok():
            return passed_order.ok()
        else:
            raise TraderException(passed_order.err())


if __name__ == "__main__":
    from aiobinance.api.account import retrieve_account
    from aiobinance.config import load_api_keyfile

    creds = load_api_keyfile()

    api = Binance(credentials=creds)  # we might need private requests here !

    account = retrieve_account(api=api, test=True)

    trader = Trader(account=account, market=account.exchange.market["COTIBNB"])

    print("Buy test order: ")
    # Decimal of float here to test precision. it should be built from string instead !
    order = trader.buy(amount=Decimal(300), total_expected=Decimal(0.45))
    print(order)  # None is expected on test

    print("Buy sell order: ")
    # Decimal of float here to test precision. it should be built from string instead !
    order = trader.sell(amount=Decimal(300), total_expected=Decimal(0.45))
    print(order)  # None is expected on test

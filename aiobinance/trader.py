from __future__ import annotations

import asyncio
import decimal
from asyncio import AbstractEventLoop
from decimal import Decimal
from typing import Optional

from aiobinance.api.account import Account
from aiobinance.api.exchange import retrieve_exchange
from aiobinance.api.market import Market
from aiobinance.api.rawapi import Binance
from aiobinance.model.ticker import Ticker


class Trader:
    def __init__(self, account: Account, market: Market):
        self.account = account
        self.market = market

        self._loop = None
        self._running = None

    def check_market(self):
        tkr = self.market.ticker24()
        print(tkr)

    # TODO :retrieve cost of asset in past trades, to determine cost...
    # TODO : some forcasting to determine opportunity...
    # TODO : then do some time-based arbitrage... hodl or fomo ?

    def sell(
        self, amount: Decimal, total_expected: Optional[Decimal] = None, test=True
    ):

        # adjusting precision
        with decimal.localcontext() as ctx:
            ctx.prec = self.market.base_asset_precision
            amount = ctx.create_decimal(amount)
        with decimal.localcontext() as ctx:
            ctx.prec = self.market.quote_asset_precision
            total_expected = ctx.create_decimal(total_expected)

        # TODO : get rid of market order, always pass limit
        #  computing price is cheap here and can save us from bait orders/crazy slippage
        if not total_expected:
            passed_order = self.market.market_order(
                side="SELL", quantity=amount, test=test
            )
        else:
            with decimal.localcontext() as ctx:
                ctx.prec = (
                    self.market.quote_precision
                )  # we want a price (unit is quote currency)
                ctx.rounding = decimal.ROUND_UP
                sell_price = ctx.divide(total_expected, amount)

            # some logic to verify price
            tkr = self.market.ticker24()

            if sell_price < tkr.ask_price:
                # Preventing selling at lower price than market
                print(
                    f"Asked price {sell_price} is below market: {tkr.ask_price}. Correcting to {tkr.ask_price}."
                )
                sell_price = tkr.ask_price

            passed_order = self.market.limit_order(
                side="SELL", quantity=amount, price=sell_price, test=test
            )
        return passed_order.value

    def buy(self, amount: Decimal, total_expected: Optional[Decimal] = None, test=True):

        # adjusting precision
        with decimal.localcontext() as ctx:
            ctx.prec = self.market.base_asset_precision
            amount = ctx.create_decimal(amount)
        with decimal.localcontext() as ctx:
            ctx.prec = self.market.quote_asset_precision
            total_expected = ctx.create_decimal(total_expected)

        # TODO : get rid of market order, always pass limit
        #  computing price is cheap here and can save us from bait orders/crazy slippage
        if not total_expected:
            passed_order = self.market.market_order(
                side="BUY", quantity=amount, test=test
            )
        else:
            with decimal.localcontext() as ctx:
                ctx.prec = (
                    self.market.quote_precision
                )  # we want a price (unit is quote currency)
                ctx.rounding = decimal.ROUND_DOWN
                buy_price = ctx.divide(total_expected, amount)

            # some logic to verify price
            tkr = self.market.ticker24()

            if buy_price > tkr.bid_price:
                # Preventing buying at a higher price than market
                print(
                    f"Bid price {buy_price} is above market: {tkr.bid_price}. Correcting to {tkr.bid_price}."
                )
                buy_price = tkr.bid_price

            passed_order = self.market.limit_order(
                side="BUY", quantity=amount, price=buy_price, test=test
            )
        return passed_order.value


if __name__ == "__main__":
    from aiobinance.api.account import retrieve_account
    from aiobinance.config import load_api_keyfile

    creds = load_api_keyfile()

    api = Binance(credentials=creds)  # we might need private requests here !

    account = retrieve_account(api=api)

    trader = Trader(account=account, market=account.exchange.market["COTIBNB"])
    trader.check_market()

    print("Buy test order: ")
    # Decimal of float here to test precision. it should be built from string instead !
    order = trader.buy(amount=Decimal(300), total_expected=Decimal(0.45), test=True)
    print(order)  # None is expected on test

    print("Buy sell order: ")
    # Decimal of float here to test precision. it should be built from string instead !
    order = trader.sell(amount=Decimal(300), total_expected=Decimal(0.45), test=True)
    print(order)  # None is expected on test

"""
Module focusing on One Immediate Trade only, with given information.
Goal here is to converge towards expected trade result and limit slippage...
"""
import decimal
from decimal import Decimal

from aiobinance.api.market import Market
from aiobinance.model import OHLCV
from aiobinance.model.order import LimitOrder
from aiobinance.model.ticker import Ticker

# TODO : maybe there should be a concept of "safe-counter" and a concept of "trade-optimizer"


# TODO : maybe depend on tinyDB to track trade and make restore&debug possible ??
#  Goal: pid controller to minimize slippage,
#  controlling order amount and price compared with requested amount and price...
class TradeConverge:
    @classmethod
    def from_ticker(cls, mkt: Market, tkr: Ticker):
        # TODO : find current price from ticker

        # adjusting precision in price
        with decimal.localcontext() as ctx:
            ctx.prec = mkt.quote_precision
            bid_price = ctx.create_decimal(tkr.bid_price)
            ask_price = ctx.create_decimal(tkr.ask_price)

        return cls(
            market=mkt,
            bid_price=bid_price,
            ask_price=ask_price,
        )

    # TODO
    # @classmethod
    # def from_ohlc(cls, mkt: Market, ohlc: OHLCV):
    #     # TODO : find current price from ohlcv
    #
    #     return cls(current_price=)

    def __init__(self, market: Market, bid_price: Decimal, ask_price: Decimal):
        """Initializes a one-time trade with immediate order.

        We try to limit side effects here:
        - known price is fixed at this stage.
        - market is only there to provide information about decimal precision, and methods to send order and receive trades.
        It can be mocked for tests (use recorded data from cassettes for this)...
        """
        # quote precision already integrated in prices.
        self.bid_price = bid_price
        self.ask_price = ask_price

        self.market = market

    async def sell(
        self, amount: Decimal, expected_gain: Decimal, test=True, post_only=True
    ) -> LimitOrder:
        # TODO : post_only (kraken) is LIMIT_MAKER on binance

        # adjusting precision
        with decimal.localcontext() as ctx:
            ctx.prec = self.market.base_asset_precision
            amount = ctx.create_decimal(amount)

        with decimal.localcontext() as ctx:
            ctx.prec = self.market.quote_asset_precision
            expected_gain = ctx.create_decimal(expected_gain)

        with decimal.localcontext() as ctx:
            ctx.prec = self.market.quote_precision
            ctx.rounding = decimal.ROUND_UP

            # check price is sensible (comparing to self.ask_price)
            sell_price = ctx.divide(expected_gain, amount)

        if sell_price < self.ask_price:
            # Preventing selling at lower price than market
            # TODO : log it !
            # print(
            #     f"Asked price {sell_price} is below market: {self.ask_price}. Correcting to {self.ask_price}."
            # )
            sell_price = self.ask_price

        # TODO : await (so other things can keep going in background...)
        passed_order = self.market.limit_order(
            side="SELL", quantity=amount, price=sell_price, test=test
        )

        # TODO try
        #  await for trade
        #  trade detected : result analysis...
        #  if exit : store result for later analysis ??

        return passed_order.value

    async def buy(
        self, amount: Decimal, expected_cost: Decimal, test=True, post_only=True
    ) -> LimitOrder:
        # TODO : post_only (kraken) is LIMIT_MAKER on binance
        # adjusting precision
        with decimal.localcontext() as ctx:
            ctx.prec = self.market.base_asset_precision
            amount = ctx.create_decimal(amount)

        with decimal.localcontext() as ctx:
            ctx.prec = self.market.quote_asset_precision
            expected_cost = ctx.create_decimal(expected_cost)

        with decimal.localcontext() as ctx:
            ctx.prec = self.market.quote_precision
            ctx.rounding = decimal.ROUND_DOWN

            # check price is sensible (comparing to self.bid_price)
            buy_price = ctx.divide(expected_cost, amount)

        if buy_price > self.bid_price:
            # Preventing buying at a higher price than market
            # TODO : log it !
            # print(
            #     f"Bid price {buy_price} is above market: {self.bid_price}. Correcting to {self.bid_price}."
            # )
            buy_price = self.bid_price

        # TODO : await (so other things can keep going in background...)
        passed_order = self.market.limit_order(
            side="BUY", quantity=amount, price=buy_price, test=test
        )

        # TODO try
        #  await for trade
        #  trade detected : result analysis...
        #  if exit : store result for later analysis ??

        return passed_order.value

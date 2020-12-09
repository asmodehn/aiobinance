"""
Module focusing on One Immediate Trade only, with given information.
Goal here is to converge towards expected trade result and limit slippage...
"""
import decimal
import typing
from decimal import Decimal
from typing import Any, Callable, Optional

from result import Err, Ok, Result

from aiobinance.api.model.order import LimitOrder, OrderSide
from aiobinance.api.pure.marketbase import MarketBase
from aiobinance.api.pure.ticker import Ticker


# TODO : review this since the separation of model and pure packages in api...
class SafeCounter:
    """This is a counter where we can pass orders.
    However it has minimal safeguards in place
    """

    @classmethod
    def from_ticker(cls, mkt: MarketBase, tkr: Ticker):
        return cls(
            bid_price=tkr.bid_price,
            ask_price=tkr.ask_price,
            base_asset_precision=mkt.info.base_asset_precision,
            quote_asset_precision=mkt.info.quote_asset_precision,
            order_callable=mkt.limit_order,
        )

    # TODO
    # @classmethod
    # def from_ohlc(cls, mkt: Market, ohlc: OHLCV):
    #     # TODO : find current price from ohlcv
    #
    #     return cls(current_price=)

    def __init__(
        self,
        bid_price: Decimal,
        ask_price: Decimal,
        base_asset_precision: int,
        quote_asset_precision: int,
        order_callable: Callable[
            [Any, Decimal, Decimal, Any, Optional[Decimal], Any],
            Result[LimitOrder, Exception],
        ],
    ):
        """Initializes a one-time trade with immediate order.

        We try to limit side effects here:
        - known price is fixed at this stage.
        - market is not stored here to prevent side effects. we only rely on an "order passing callable"
        """
        # quote precision already integrated in prices.

        # adjusting precision in price
        with decimal.localcontext() as ctx:
            ctx.prec = quote_asset_precision
            self.bid_price = ctx.create_decimal(bid_price)
            self.ask_price = ctx.create_decimal(ask_price)

        self.base_asset_precision = base_asset_precision
        self.quote_asset_precision = quote_asset_precision

        self.limit_order = order_callable

    async def sell(
        self, amount: Decimal, expected_gain: Decimal, post_only=True
    ) -> Result[typing.Union[LimitOrder, None], Exception]:
        # TODO : post_only (kraken) is LIMIT_MAKER on binance

        if amount.is_zero():
            return Ok(None)

        # adjusting precision
        with decimal.localcontext() as ctx:
            ctx.prec = self.base_asset_precision
            amount = ctx.create_decimal(amount)

        with decimal.localcontext() as ctx:
            ctx.prec = self.quote_asset_precision
            expected_gain = ctx.create_decimal(expected_gain)
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
        passed_order = self.limit_order(
            side=OrderSide.SELL, quantity=amount, price=sell_price
        )

        #  TODO: await for trade
        #   trade detected : result analysis...
        return passed_order

    async def buy(
        self, amount: Decimal, expected_cost: Decimal, post_only=True
    ) -> Result[typing.Union[LimitOrder, None], Exception]:

        if amount.is_zero():
            return Ok(None)

        # TODO : post_only (kraken) is LIMIT_MAKER on binance
        # adjusting precision
        with decimal.localcontext() as ctx:
            ctx.prec = self.base_asset_precision
            amount = ctx.create_decimal(amount)

        with decimal.localcontext() as ctx:
            ctx.prec = self.quote_asset_precision
            expected_cost = ctx.create_decimal(expected_cost)
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
        passed_order = self.limit_order(
            side=OrderSide.BUY, quantity=amount, price=buy_price
        )

        #  TODO: await for trade
        #   trade detected : result analysis...
        return passed_order

    # TODO ?
    # async def trades(self):
    #
    #     # wait for trades, only from passed order via this counter.
    #     self.

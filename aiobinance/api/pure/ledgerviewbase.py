from __future__ import annotations

from datetime import datetime
from typing import Optional, Union

import hypothesis.strategies as st

from aiobinance.api.model.account_info import AssetAmount
from aiobinance.api.model.asset_info import AssetInfo
from aiobinance.api.model.trade import Trade
from aiobinance.api.model.tradeframe import TradeFrame
from aiobinance.api.pure.tradesviewbase import TradesViewBase


class LedgerViewBase:

    # ledger is completely dependent on trades on binance (no Ledger API ?)

    coin: AssetInfo  # TODO : improve this...
    amount: AssetAmount  # TODO :maybe this could be calculated from ledger, and compared to the Accountamount (might not be same ?)
    trades: dict[str, TradeFrame]
    # TODO : the str (coin like "BTC") could be in types, or in units (cf. pint)

    @st.composite
    @staticmethod
    def strategy(draw, max_size=5):
        coin = draw(
            AssetInfo.strategy()
        )  # TODO : link a coin with matching markets (as base or quote)
        amount = draw(AssetAmount.strategy())
        # using maxsize for both because why not...
        frames = draw(
            st.lists(elements=TradeFrame.strategy(max_size=max_size), max_size=max_size)
        )
        return LedgerViewBase(coin, amount, *frames)

    @property
    def balances(self):
        return self.amount  # TODO be able to compute this from ledger as well...

    def __init__(self, coin: AssetInfo, amount: AssetAmount, *frames: TradeFrame):
        self.coin = coin  # TMP: currently user is supposed to match coin with symbols in tradeframes... TODO : enforce it
        self.amount = amount
        self.trades = {f.symbol: f for f in frames}

    def __call__(
        self,
        *frames: TradeFrame,
        **kwargs  # TODO : Make a LedgerFrame, and link with tradeframe at a lower level...
    ) -> LedgerViewBase:
        """ self updating the instance with new dataframe..."""
        # return same instance if no change
        if len(frames) is None:
            return self

        # updating by merging data for same symbol...
        self.trades.update(
            {
                f.symbol: self.trades[f.symbol].union(f)
                if f.symbol in self.trades
                else f
                for f in frames
            }
        )

        # returning self to allow chaining
        return self

    # Exposing mapping interface on continuous time index
    # TODO:  a LedgerFRame just like we have a TradeFrame, with appropriate columns...

    def __contains__(self, item: Union[Trade, int, datetime]) -> bool:
        # https://docs.python.org/2/reference/datamodel.html#object.__contains__

        for sym in self.trades.keys():
            if item in self.trades[sym]:
                return True
        return False  # false if it was not found anywhere

    def __eq__(self, other: LedgerViewBase) -> bool:
        assert isinstance(
            other, LedgerViewBase
        )  # in our design the type infers the columns.
        if self is other:
            # here we follow python on equality https://docs.python.org/3.6/reference/expressions.html#id12
            return True
        else:  # delegate equality to the unique member: trades
            return self.trades == other.trades

    def __getitem__(
        self, item: Union[int, datetime, slice]
    ) -> Union[LedgerViewBase, Trade]:

        frames = []
        for sym in self.trades.keys():
            res = self.trades[sym][item]
            if isinstance(res, TradeFrame):
                frames.append(res)
            else:
                return res
        return LedgerViewBase(self.coin, self.amount, *frames)

    # NO SETTING ON TRADES :they are immutable events.

    def __iter__(self):
        yield from [self.trades[sym] for sym in self.trades]

    # TODO : aiter

    def __len__(self):
        return sum(len(self.trades[sym]) for sym in self.trades.keys())

    def __str__(self):
        return str(self.trades)


if __name__ == "__main__":

    print(LedgerViewBase.strategy().filter(lambda e: len(e.trades) >= 1).example())

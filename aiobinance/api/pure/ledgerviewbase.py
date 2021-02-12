from __future__ import annotations

from datetime import datetime
from typing import Dict, Optional, Union

import hypothesis.strategies as st

from aiobinance.api.model.account_info import AssetAmount
from aiobinance.api.model.asset_info import AssetInfo
from aiobinance.api.model.trade import Trade
from aiobinance.api.model.tradeframe import TradeFrame
from aiobinance.api.pure.tradesviewbase import TradesViewBase


class LedgerViewBase:

    # ledger is completely dependent on trades on binance (no Ledger API ?)

    coininfo: Optional[
        AssetInfo
    ]  # TODO : improve this... Note : it is not mandatory (some coins dont have info on binance...??)

    # TODO : cleaner handling of base and quote trades...
    base_trades: Dict[str, TradesViewBase]
    quote_trades: Dict[str, TradesViewBase]
    # TODO : the str (coin like "BTC") could be in types, or in units (cf. pint)

    @st.composite
    @staticmethod
    def strategy(draw, max_size=5):
        coin = draw(
            st.one_of(st.none(), AssetInfo.strategy())
        )  # TODO : link a coin with matching markets (as base or quote)
        # using maxsize for both because why not...
        base_trades = draw(
            st.dictionaries(
                keys=st.text(min_size=2, max_size=8),
                values=TradesViewBase.strategy(max_size=max_size),
                max_size=max_size,
            )
        )
        quote_trades = draw(
            st.dictionaries(
                keys=st.text(min_size=2, max_size=8),
                values=TradesViewBase.strategy(max_size=max_size),
                max_size=max_size,
            )
        )
        return LedgerViewBase(coin, base_trades, quote_trades)

    def __init__(
        self,
        coin: Optional[AssetInfo] = None,
        base_trades: Dict[str, TradesViewBase] = None,
        quote_trades: Dict[str, TradesViewBase] = None,
    ):
        self.coininfo = coin  # TMP: currently user is supposed to match coin with symbols in tradeframes... TODO : enforce it

        # TODO : what if no trades? we should plan with existing markets...
        self.base_trades = {} if base_trades is None else base_trades
        self.quote_trades = {} if quote_trades is None else quote_trades

    def __call__(
        self,
        base_trades: Dict[str, TradesViewBase] = None,
        quote_trades: Dict[str, TradesViewBase] = None,
        **kwargs,  # TODO : Make a LedgerFrame, and link with tradeframe at a lower level...
    ) -> LedgerViewBase:
        """ self updating the instance with new tradesview..."""

        # Note : this will replace the tradeviews... # TODO : use ledgerframe
        self.base_trades.update({f.symbol: f for f in base_trades.values()})

        self.quote_trades.update({f.symbol: f for f in quote_trades.values()})

        # returning self to allow chaining
        return self

    # Exposing mapping interface on continuous time index
    # TODO:  a LedgerFrame just like we have a TradeFrame, with appropriate columns...

    def __contains__(self, item: Union[Trade, int, datetime]) -> bool:
        # https://docs.python.org/2/reference/datamodel.html#object.__contains__

        for sym in self.base_trades.keys():
            if item in self.base_trades[sym]:
                return True
        for sym in self.quote_trades.keys():
            if item in self.quote_trades[sym]:
                return True
        return False  # false if it was not found anywhere

    def __eq__(self, other: LedgerViewBase) -> bool:
        assert isinstance(
            other, LedgerViewBase
        )  # in our design the type infers the columns.
        if self is other:
            # here we follow python on equality https://docs.python.org/3.6/reference/expressions.html#id12
            return True
        else:  # delegate equality to the members: trades
            return (
                self.base_trades == other.base_trades
                and self.quote_trades == other.quote_trades
            )

    def __getitem__(
        self, item: Union[str, slice]
    ) -> Union[LedgerViewBase, TradesViewBase, Trade]:

        if isinstance(item, str):  # assume symbol
            if item in self.base_trades.keys():
                return self.base_trades[item]
            if item in self.quote_trades.keys():
                return self.quote_trades[item]

        # otherwise (different kind of slices...)
        elif isinstance(item, slice):
            base_trades = {}
            for sym in self.base_trades.keys():
                res = self.base_trades[sym][item]
                if isinstance(res, TradesViewBase):
                    base_trades[sym] = res
                else:
                    return res  # single Trade case ?

            quote_trades = {}
            for sym in self.quote_trades.keys():
                res = self.quote_trades[sym][item]
                if isinstance(res, TradesViewBase):
                    quote_trades[sym] = res
                else:
                    return res  # single Trade case ?

            return LedgerViewBase(self.coininfo, base_trades, quote_trades)
        else:
            raise RuntimeError(f"item {item} not supported !")

    def __iter__(self):
        yield from [self.base_trades[sym] for sym in self.base_trades]
        yield from [self.quote_trades[sym] for sym in self.quote_trades]

    # TODO : aiter

    def __len__(self):
        return sum(
            *[len(self.base_trades[sym]) for sym in self.base_trades.keys()],
            *[len(self.quote_trades[sym]) for sym in self.quote_trades.keys()],
        )

    def __str__(self):
        return str(self.base_trades) + str(self.quote_trades)


if __name__ == "__main__":

    print(LedgerViewBase.strategy().filter(lambda e: len(e.trades) >= 1).example())

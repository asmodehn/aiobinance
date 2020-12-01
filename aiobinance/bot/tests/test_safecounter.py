from __future__ import annotations

import asyncio
import unittest
from decimal import Decimal
from typing import Optional

import hypothesis.strategies as st
from hypothesis import given
from result import Ok, Result

from aiobinance.api.model.order import LimitOrder
from aiobinance.api.pure.puremarket import PureMarket
from aiobinance.api.pure.ticker import Ticker, st_ticker
from aiobinance.bot.safecounter import SafeCounter


@st.composite
def st_safecounter(draw):
    # large possible precision interval
    base_prec = draw(st.integers(min_value=3, max_value=14))
    quote_prec = draw(st.integers(min_value=3, max_value=14))

    bid_price = draw(
        st.decimals(
            min_value="0.0001",
            max_value="1000.0000",
            allow_nan=False,
            allow_infinity=False,
        )
    )
    ask_pct_bid = draw(
        st.decimals(
            min_value="1.001",
            max_value="1.10",
            allow_nan=False,
            allow_infinity=False,
        )
    )  # picking 0.1% min and 10% max of delta between bid and ask

    pm = draw(PureMarket.strategy())

    return SafeCounter(
        bid_price=bid_price,
        ask_price=bid_price * ask_pct_bid,
        base_asset_precision=base_prec,
        quote_asset_precision=quote_prec,
        order_callable=pm.limit_order,
    )


class TestSafeCounter(unittest.TestCase):
    @given(
        counter=st_safecounter(),
        amount=st.decimals(min_value=0, allow_infinity=False, allow_nan=False),
        gain=st.decimals(min_value=0, allow_nan=False, allow_infinity=False),
    )
    def test_sell(self, counter, amount, gain):
        res = asyncio.run(counter.sell(amount=amount, expected_gain=gain))
        if amount.is_zero():
            assert res.ok() is None
        else:
            value = res.ok()
            assert isinstance(value, LimitOrder)

    # TODO post_only/LIMIT_MAKER test

    @given(
        counter=st_safecounter(),
        amount=st.decimals(min_value=0, allow_infinity=False, allow_nan=False),
        cost=st.decimals(min_value=0, allow_nan=False, allow_infinity=False),
    )
    def test_buy(self, counter, amount, cost):
        res = asyncio.run(counter.buy(amount=amount, expected_cost=cost))
        if amount.is_zero():
            assert res.ok() is None
        else:
            value = res.ok()
            assert isinstance(value, LimitOrder)

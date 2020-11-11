import dataclasses
import unittest

import hypothesis.strategies as st
from hypothesis import given

from aiobinance.model.trade import (
    EmptyTradeFrame,
    Trade,
    TradeFrame,
    st_tradeframes,
    st_trades,
)


class TestTrade(unittest.TestCase):
    @given(trade=st_trades())
    def test_str(self, trade: Trade):
        # Check sensible information is displayed (order doesnt matter for output to human)
        trade_str = str(trade)
        assert f"time: {str(trade.time)}" in trade_str
        assert f"symbol: {str(trade.symbol)}" in trade_str
        assert f"id: {str(trade.id)}" in trade_str
        assert f"price: {str(trade.price)}" in trade_str
        assert f"qty: {str(trade.qty)}" in trade_str
        assert f"quote_qty: {str(trade.quote_qty)}" in trade_str
        assert (
            f"commission: {str(trade.commission)} {trade.commission_asset}" in trade_str
        )
        assert f"is_buyer: {str(trade.is_buyer)}" in trade_str
        assert f"is_maker: {str(trade.is_maker)}" in trade_str
        assert f"order_id: {str(trade.order_id)}" in trade_str
        assert f"order_list_id: {str(trade.order_list_id)}" in trade_str
        assert f"is_best_match: {str(trade.is_best_match)}" in trade_str

    @given(trade=st_trades())
    def test_dir(self, trade: Trade):
        # check all information is exposed
        expected = {
            "time",
            "symbol",
            "id",
            "price",
            "qty",
            "quote_qty",
            "commission",
            "commission_asset",
            "is_buyer",
            "is_maker",
            "order_id",
            "order_list_id",
            "is_best_match",
        }
        assert {a for a in dir(trade)}.issuperset(expected), expected.difference(
            {a for a in dir(trade)}
        )

        # check no extra information is exposed
        assert {a for a in dir(trade) if not a.startswith("__")}.issubset(expected), {
            a for a in dir(trade) if not a.startswith("__")
        }.difference(expected)


# test TradeFrame (should have columns even empty)
class TestTradeFrame(unittest.TestCase):
    @given(tradeframe=st_tradeframes())
    def test_sequence(self, tradeframe: TradeFrame):
        # test we can iterate on contained data, and that length matches. Ref : https://docs.python.org/3/library/collections.abc.html
        tfl = len(tradeframe)  # __len__

        counter = 0
        decount = -tfl
        for t in tradeframe:  # __iter__
            assert isinstance(t, Trade)
            assert t in tradeframe  # __contains__
            assert tradeframe[counter] == t  # __getitem__ on index
            assert tradeframe[decount] == t  # __getitem on negative index
            assert tradeframe[t.id] == t  # __getitem__ on id (mapping-like)
            counter += 1
            decount += 1

        assert counter == tfl

    @given(tradeframe=st_tradeframes(), data=st.data())
    def test_container(self, tradeframe: TradeFrame, data):
        # This completes the test_sequence to verify "directed container" semantics (as per Danel Ahman's paper)
        assert (
            isinstance(tradeframe[0:0], TradeFrame) and len(tradeframe[0:0]) == 0
        )  # empty tradeframe slice

        if len(tradeframe) > 0:
            assert (
                tradeframe[0 : len(tradeframe)] is tradeframe
            )  # whole slice is the same thing

            sidx1 = data.draw(
                st.one_of(
                    st.none(), st.integers(min_value=0, max_value=len(tradeframe))
                )
            )
            sidx2 = data.draw(
                st.one_of(
                    st.none(), st.integers(min_value=sidx1, max_value=len(tradeframe))
                )
            )

            if sidx1 is None or sidx2 is None or sidx1 <= sidx2:
                sliced = tradeframe[sidx1:sidx2]
                if sidx1 is not None and sidx1 == sidx2:  # implies sidx is not None
                    assert sliced is EmptyTradeFrame
                elif sidx1 is None or sidx1 == 0:
                    if sidx2 is None or sidx2 > len(tradeframe):
                        assert sliced is tradeframe
                counter = sidx1 if sidx1 is not None else 0
            else:
                sliced = tradeframe[sidx2:sidx1]
                if sidx2 is None or sidx2 == 0:
                    if sidx1 is None or sidx1 > len(tradeframe):
                        assert sliced is tradeframe
                counter = sidx2 if sidx2 is not None else 0
            assert isinstance(sliced, TradeFrame)

            for t in sliced:
                assert t == tradeframe[counter]
                counter += 1
        else:
            assert tradeframe is EmptyTradeFrame
            assert tradeframe[0 : len(tradeframe)] is EmptyTradeFrame

    @given(tradeframe=st_tradeframes())
    def test_str(self, tradeframe: TradeFrame):
        # Check sensible information is displayed (order doesnt matter for output to human)

        # we rely on optimize the tradeframe to drop compute details
        # opttf = tradeframe.optimized()

        tf_str = str(tradeframe)  # but we still call str on the frame
        tf_header = tf_str.split("\n")[1]
        for f in dataclasses.fields(Trade):
            # check headers
            assert f.name in tf_header
        # TODO : build mapping for output comparison here ??

        # TODO : compare values displayed (tricky)
        # for t, s in zip(opttf.itertuples(), tf_str.split('\n')[3:-1]):
        #     # check content by comparing with simplified data
        #     for f in dataclasses.fields(Trade):
        #         attr_val = getattr(t, f.name)
        #         if attr_val is not None:  # optional attr case
        #             assert str(attr_val) in s, f.name

    # TODO
    # @given(tradeframe=st_tradeframes())
    # def test_optimized(self, tradeframe: TradeFrame):
    #
    #
    #
    #     raise NotImplementedError

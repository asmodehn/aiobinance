import dataclasses
import unittest

import hypothesis.strategies as st
from hypothesis import assume, given

from aiobinance.api.model.trade import Trade
from aiobinance.api.model.tradeframe import TradeFrame
from aiobinance.api.pure.tradesviewbase import TradesViewBase


# test TradeFrame (should have columns even empty)
class TestTradesViewBase(unittest.TestCase):
    @given(ohlcview=TradesViewBase.strategy())
    def test_strategy(self, ohlcview: TradesViewBase):
        assert isinstance(ohlcview, TradesViewBase)
        # TODO

    @given(tradesview=TradesViewBase.strategy())
    def test_eq_mapping(self, tradesview: TradesViewBase):
        assert tradesview == tradesview
        # taking a copy via slice and comparing
        assert tradesview == tradesview[:]

    @given(tradesview=TradesViewBase.strategy(), data=st.data())
    def test_call(self, tradesview: TradesViewBase, data):

        tradeframe_new = data.draw(
            TradeFrame.strategy(symbols=st.just(tradesview.symbol))
        )

        # old_df = tradeframe.df.copy(deep=True)
        # old_id = tradeframe.id

        old_frame = tradesview.frame
        tradesview(frame=tradeframe_new)

        # dataframe merging happened (details handled by Tradeframe)
        if old_frame.empty:
            assert tradesview.frame == tradeframe_new
        elif tradeframe_new.empty:
            assert tradesview.frame == old_frame
        else:
            assert min(tradesview.id) == min(old_frame.id + tradeframe_new.id)
            assert max(tradesview.id) == max(old_frame.id + tradeframe_new.id)

    @given(tradesview=TradesViewBase.strategy())
    def test_str(self, tradesview: TradesViewBase):
        # Check sensible information is displayed (order doesnt matter for output to human)

        # we rely on optimize the tradeframe to drop compute details
        # opttf = tradeframe.optimized()

        tf_str = str(tradesview)  # but we still call str on the frame
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

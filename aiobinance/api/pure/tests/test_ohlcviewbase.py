import dataclasses
import unittest
from datetime import timedelta

import hypothesis.strategies as st
from hypothesis import assume, given

from aiobinance.api.model.ohlcframe import OHLCFrame
from aiobinance.api.model.pricecandle import PriceCandle
from aiobinance.api.pure.ohlcviewbase import OHLCViewBase


# test OHLCViewBase (should have columns even empty)
class TestOHLCViewBase(unittest.TestCase):
    @given(ohlcview=OHLCViewBase.strategy())
    def test_strategy(self, ohlcview: OHLCViewBase):
        assert isinstance(ohlcview, OHLCViewBase)
        # TODO

    @given(ohlcview=OHLCViewBase.strategy())
    def test_eq(self, ohlcview: OHLCViewBase):
        assert ohlcview == ohlcview
        # taking a copy via slice and comparing
        assert ohlcview == ohlcview[:]

    @given(ohlcview=OHLCViewBase.strategy(), ohlcframe_new=OHLCFrame.strategy())
    def test_call(self, ohlcview: OHLCViewBase, ohlcframe_new: OHLCFrame):

        # old_df = tradeframe.df.copy(deep=True)
        # old_id = tradeframe.id

        ohlcview(frame=ohlcframe_new)

        # after update, frames are equal
        assert ohlcview.frame == ohlcframe_new

    @given(ohlcview=OHLCViewBase.strategy())
    def test_str(self, ohlcview: OHLCViewBase):
        # TODO : this might be more specific than OHLCFrame...

        # Check sensible information is displayed (order doesnt matter for output to human)

        # we rely on optimize the tradeframe to drop compute details
        # opttf = tradeframe.optimized()

        tf_str = str(ohlcview)  # but we still call str on the frame
        tf_header = tf_str.split("\n")[1]
        for f in dataclasses.fields(PriceCandle):
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

import dataclasses
import unittest

import hypothesis.strategies as st
from hypothesis import assume, given

from aiobinance.api.model.trade import Trade
from aiobinance.api.model.tradeframe import TradeFrame
from aiobinance.api.pure.ledgerviewbase import LedgerViewBase


# test TradeFrame (should have columns even empty)
class TestLedgerViewBase(unittest.TestCase):
    @given(ledgerview=LedgerViewBase.strategy())
    def test_strategy(self, ledgerview: LedgerViewBase):
        assert isinstance(ledgerview, LedgerViewBase)
        # TODO

    @given(ledgerview=LedgerViewBase.strategy())
    def test_eq_mapping(self, ledgerview: LedgerViewBase):
        assert ledgerview == ledgerview
        # taking a copy via slice and comparing
        assert ledgerview == ledgerview[:]

    @given(ledgerview=LedgerViewBase.strategy(), data=st.data())
    def test_call(self, ledgerview: LedgerViewBase, data):

        tradeframes_new = {
            f.symbol: f for f in data.draw(st.lists(TradeFrame.strategy(), max_size=5))
        }

        # old_df = tradeframe.df.copy(deep=True)
        # old_id = tradeframe.id

        old_frames = ledgerview.trades
        ledgerview(*tradeframes_new.values())

        # dataframe merging happened (details handled by Tradeframe)
        if len(old_frames) == 0:
            assert ledgerview.trades == tradeframes_new
        elif len(tradeframes_new) == 0:
            assert ledgerview.trades == old_frames
        else:
            for sym, frame in ledgerview.trades.items():
                old = old_frames.get(sym, None)
                frames = TradeFrame(symbol=sym)
                for f in tradeframes_new.values():
                    if f.symbol == sym:
                        frames = frames.union(f)

                if old is None or old.empty:
                    assert frame == frames
                elif frames.empty:
                    assert frame == old  # no change
                else:
                    # union happened properly
                    assert min(frame.id) == min(old.id + frames.id)
                    assert max(frame.id) == max(old.id + frames.id)

    # TODO : what representation we want here ?
    # @given(ledgerview=LedgerViewBase.strategy())
    # def test_str(self, ledgerview: LedgerViewBase):
    #     # Check sensible information is displayed (order doesnt matter for output to human)
    #
    #     # we rely on optimize the tradeframe to drop compute details
    #     # opttf = tradeframe.optimized()
    #
    #     tf_str = str(ledgerview)  # but we still call str on the frame
    #     tf_header = tf_str.split("\n")[1]
    #     for f in dataclasses.fields(Trade):
    #         # check headers
    #         assert f.name in tf_header
    #     # TODO : build mapping for output comparison here ??
    #
    #     # TODO : compare values displayed (tricky)
    #     # for t, s in zip(opttf.itertuples(), tf_str.split('\n')[3:-1]):
    #     #     # check content by comparing with simplified data
    #     #     for f in dataclasses.fields(Trade):
    #     #         attr_val = getattr(t, f.name)
    #     #         if attr_val is not None:  # optional attr case
    #     #             assert str(attr_val) in s, f.name
    #
    # # TODO
    # # @given(tradeframe=st_tradeframes())
    # # def test_optimized(self, tradeframe: TradeFrame):
    # #
    # #
    # #
    # #     raise NotImplementedError

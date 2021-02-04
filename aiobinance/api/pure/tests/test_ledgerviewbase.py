import dataclasses
import unittest

import hypothesis.strategies as st
from hypothesis import HealthCheck, assume, given, settings

from aiobinance.api.pure.ledgerviewbase import LedgerViewBase
from aiobinance.api.pure.tradesviewbase import TradesViewBase


class TestLedgerViewBase(unittest.TestCase):
    @given(ledgerview=LedgerViewBase.strategy())
    @settings(suppress_health_check=[HealthCheck.too_slow])
    def test_strategy(self, ledgerview: LedgerViewBase):
        assert isinstance(ledgerview, LedgerViewBase)
        # TODO

    @given(ledgerview=LedgerViewBase.strategy())
    @settings(suppress_health_check=[HealthCheck.too_slow])
    def test_eq_mapping(self, ledgerview: LedgerViewBase):
        assert ledgerview == ledgerview
        # taking a copy via slice and comparing
        assert ledgerview == ledgerview[:]

    @given(ledgerview=LedgerViewBase.strategy(), data=st.data())
    @settings(suppress_health_check=[HealthCheck.too_slow])
    def test_call(self, ledgerview: LedgerViewBase, data):

        old_base = ledgerview.base_trades.copy()
        old_quote = ledgerview.quote_trades.copy()

        base_tradeview_new = {
            f.symbol: f
            for f in data.draw(st.lists(TradesViewBase.strategy(), max_size=5))
        }
        quote_tradeview_new = {
            f.symbol: f
            for f in data.draw(st.lists(TradesViewBase.strategy(), max_size=5))
        }

        ledgerview(base_trades=base_tradeview_new, quote_trades=quote_tradeview_new)

        # we merge tradeviews in the dictionnary, but not the tradeframes
        for sym, tv in base_tradeview_new.items():
            assert sym in ledgerview.base_trades.keys()
            assert ledgerview.base_trades[sym] == tv

        for sym, tv in quote_tradeview_new.items():
            assert sym in ledgerview.quote_trades.keys()
            assert ledgerview.quote_trades[sym] == tv

        # old views are still there if symbol didnt match
        for sym, tv in old_base.items():
            if sym not in base_tradeview_new:
                assert sym in ledgerview.base_trades
                assert ledgerview.base_trades[sym] == tv

        for sym, tv in old_quote.items():
            if sym not in quote_tradeview_new:
                assert sym in ledgerview.quote_trades
                assert ledgerview.quote_trades[sym] == tv

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

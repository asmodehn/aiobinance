import dataclasses
import unittest

import hypothesis.strategies as st
from hypothesis import given

from aiobinance.api.model.ohlcframe import OHLCFrame
from aiobinance.api.model.pricecandle import PriceCandle


class TestOHLCV(unittest.TestCase):
    @given(ohlcframe=OHLCFrame.strategy())
    def test_eq_sequence(self, ohlcframe: OHLCFrame):
        assert ohlcframe == ohlcframe
        # taking a copy via slice and comparing
        assert ohlcframe == ohlcframe[:]

    @given(ohlcframe=OHLCFrame.strategy(), data=st.data())
    def test_index_sequence(self, ohlcframe: OHLCFrame, data):
        # test we can iterate on contained data, and that length matches.
        # Ref : https://docs.python.org/3/library/collections.abc.html
        tfl = len(ohlcframe)  # __len__

        counter = 0
        decount = -tfl
        for c in ohlcframe:  # __iter__
            assert isinstance(c, PriceCandle)
            assert c in ohlcframe  # __contains__
            assert ohlcframe[counter] == c  # __getitem__ on index in sequence
            assert ohlcframe[decount] == c  # __getitem on negative index in sequence
            counter += 1
            decount += 1

        assert counter == tfl

        with self.assertRaises(KeyError) as exc:
            rid = data.draw(
                st.one_of(
                    st.integers(max_value=-len(ohlcframe) - 1),
                    st.integers(min_value=len(ohlcframe)),
                )
            )
            ohlcframe[rid]
        assert isinstance(exc.exception, KeyError)

    @given(ohlcframe=OHLCFrame.strategy(), data=st.data())
    def test_slice_sequence(self, ohlcframe: OHLCFrame, data):
        # test we can iterate on contained data, and that length matches.
        # Ref : https://docs.python.org/3/library/collections.abc.html
        tfl = len(ohlcframe)  # __len__

        sss = data.draw(st.integers(min_value=-tfl, max_value=tfl))
        if sss < 0:  # negative indexing on slices
            s = slice(data.draw(st.integers(min_value=-tfl, max_value=sss)), sss)
        else:
            s = slice(sss, data.draw(st.integers(min_value=sss, max_value=tfl)))

        tfs = ohlcframe[s]
        assert isinstance(tfs, OHLCFrame)
        assert (
            len(tfs) == s.stop - s.start
        ), f" len(tfs)!= s.stop - s.start : {len(tfs)} != {s.stop - s.start}"

        counter = s.start
        for c in tfs:  # __iter__
            assert isinstance(c, PriceCandle)
            assert c in ohlcframe  # value present in origin check
            assert ohlcframe[counter] == c  # same value as origin via equality check
            counter += 1

        assert counter - s.start == len(
            tfs
        ), f"counter-s.start != len(tfs) : {counter-s.start} != {len(tfs)}"

        # test larger slice
        s = slice(
            data.draw(st.integers(max_value=-tfl)),
            data.draw(st.integers(min_value=tfl)),
        )
        assert ohlcframe[s] == ohlcframe
        # making sure we have the usual copy behavior when taking slices
        assert ohlcframe[s] is not ohlcframe

    @given(ohlcv=OHLCFrame.strategy())
    def test_str(self, ohlcv: OHLCFrame):
        # Check sensible information is displayed (order doesnt matter for output to human)

        # we rely on optimize the tradeframe to drop compute details
        # opttf = tradeframe.optimized()

        tf_str = str(ohlcv)  # but we still call str on the frame
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

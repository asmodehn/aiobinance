import dataclasses
import unittest

import hypothesis.strategies as st
from hypothesis import given

from aiobinance.api.model.trade import Trade
from aiobinance.api.model.tradeframe import TradeFrame


# test TradeFrame (should have columns even empty)
class TestTradeFrame(unittest.TestCase):
    @given(
        trade1=st.one_of(st.none(), Trade.strategy()),
        trade2=st.one_of(st.none(), Trade.strategy()),
    )
    def test_from_tradeslist(self, trade1, trade2):

        if trade1 is not None and trade2 is not None:
            tf = TradeFrame.from_tradeslist(trade1, trade2)
        elif trade2 is not None:
            tf = TradeFrame.from_tradeslist(trade2)
        elif trade1 is not None:
            tf = TradeFrame.from_tradeslist(trade1)
        else:
            tf = TradeFrame.from_tradeslist()

        # making sure the dataframe dtypes are the ones specified by the record type
        # careful : pandas may optimize these...
        for fdt, cdt in zip(tf.df.dtypes.items(), Trade.as_dtype()):
            assert fdt[0] == cdt[0]
            # dtype should be same or provide safe conversion
            assert fdt[1] == cdt[1] or fdt[1] < cdt[1]

    @given(tradeframe=TradeFrame.strategy())
    def test_eq_sequence(self, tradeframe: TradeFrame):
        assert tradeframe == tradeframe
        # taking a copy via slice and comparing
        assert tradeframe == tradeframe[:]

    @given(tradeframe=TradeFrame.strategy(), data=st.data())
    def test_index_sequence(self, tradeframe: TradeFrame, data):
        # test we can iterate on contained data, and that length matches.
        # Ref : https://docs.python.org/3/library/collections.abc.html
        tfl = len(tradeframe)  # __len__

        counter = 0
        decount = -tfl
        for t in tradeframe:  # __iter__
            assert isinstance(t, Trade)
            assert t in tradeframe  # __contains__
            assert tradeframe[counter] == t  # __getitem__ on index in sequence
            assert tradeframe[decount] == t  # __getitem on negative index in sequence
            counter += 1
            decount += 1

        assert counter == tfl

        with self.assertRaises(KeyError) as exc:
            rid = data.draw(
                st.one_of(
                    st.integers(max_value=-len(tradeframe) - 1),
                    st.integers(min_value=len(tradeframe)),
                )
            )
            tradeframe[rid]
        assert isinstance(exc.exception, KeyError)

    @given(tradeframe=TradeFrame.strategy(), data=st.data())
    def test_slice_sequence(self, tradeframe: TradeFrame, data):
        # test we can iterate on contained data, and that length matches.
        # Ref : https://docs.python.org/3/library/collections.abc.html
        tfl = len(tradeframe)  # __len__

        sss = data.draw(st.integers(min_value=-tfl, max_value=tfl))
        if sss < 0:  # negative indexing on slices
            s = slice(data.draw(st.integers(min_value=-tfl, max_value=sss)), sss)
        else:
            s = slice(sss, data.draw(st.integers(min_value=sss, max_value=tfl)))

        tfs = tradeframe[s]
        assert isinstance(tfs, TradeFrame)
        assert (
            len(tfs) == s.stop - s.start
        ), f" len(tfs)!= s.stop - s.start : {len(tfs)} != {s.stop - s.start}"

        counter = s.start
        for t in tfs:  # __iter__
            assert isinstance(t, Trade)
            assert t in tradeframe  # value present in origin check
            assert tradeframe[counter] == t  # same value as origin via equality check
            counter += 1

        assert counter - s.start == len(
            tfs
        ), f"counter-s.start != len(tfs) : {counter-s.start} != {len(tfs)}"

        # test larger slice
        s = slice(
            data.draw(st.integers(max_value=-tfl)),
            data.draw(st.integers(min_value=tfl)),
        )
        assert tradeframe[s] == tradeframe
        # making sure we have the usual copy behavior when taking slices
        assert tradeframe[s] is not tradeframe

    @given(tf1=TradeFrame.strategy(), tf2=TradeFrame.strategy())
    def test_add_sequence(self, tf1, tf2):

        tfr = tf1 + tf2

        # special case where one of them is empty
        if len(tf2) == 0:
            assert tfr == tf1
            assert (
                tfr is not tf1
            )  # we get a copy, not the same frame ( in case it gets modified somehow...)
        if len(tf1) == 0:
            assert tfr == tf2
            assert (
                tfr is not tf2
            )  # we get a copy, not the same frame ( in case it gets modified somehow...)

        assert len(tfr) == len(tf1) + len(tf2)

        # all there, keeping original ordering
        counter = 0
        for t in tf1:
            assert isinstance(t, Trade)
            assert t in tfr
            assert tfr[counter] == t
            counter += 1

        # countinuing with second frame
        counter = len(tf1)
        for t in tf2:
            assert isinstance(t, Trade)
            assert t in tfr
            assert tfr[counter] == t
            counter += 1

    @given(tradeframe=TradeFrame.strategy())
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

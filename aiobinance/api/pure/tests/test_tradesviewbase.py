import dataclasses
import unittest

import hypothesis.strategies as st
from hypothesis import assume, given

from aiobinance.api.model.trade import Trade
from aiobinance.api.model.tradeframe import TradeFrame
from aiobinance.api.pure.tradesviewbase import TradesViewBase


# test TradeFrame (should have columns even empty)
class TestTradesViewBase(unittest.TestCase):
    @given(tradesview=TradesViewBase.strategy())
    def test_eq_mapping(self, tradesview: TradesViewBase):
        assert tradesview == tradesview
        # taking a copy via slice and comparing
        assert tradesview == tradesview[:]

    @given(tradesview=TradesViewBase.strategy(), data=st.data())
    def test_index_mapping(self, tradesview: TradesViewBase, data):
        # test we can iterate on contained data, and that length matches.
        # Ref : https://docs.python.org/3/library/collections.abc.html
        tfl = len(tradesview)  # __len__

        counter = 0
        for t in tradesview:  # __iter__
            assert isinstance(t, Trade)
            assert t in tradesview  # __contains__
            assert tradesview[t.id] == t  # __getitem__ on index in mapping
            counter += 1

        assert counter == tfl

        # TODO: bounding index to what C long (pandas optimization) can handle
        rid = data.draw(st.integers())
        assume(rid not in tradesview.id)
        with self.assertRaises(KeyError) as exc:
            tradesview[rid]
        assert isinstance(exc.exception, KeyError)

    @given(tradesview=TradesViewBase.strategy(), data=st.data())
    def test_slice_mapping(self, tradesview: TradesViewBase, data):
        # test we can iterate on contained data, and that length matches.
        # Ref : https://docs.python.org/3/library/collections.abc.html

        # taking slice bounds to possibly englobe all ids, and a bit more...
        sb1 = data.draw(
            st.integers(
                min_value=max(TradeFrame.id_min(), min(tradesview.id) - 1),
                max_value=min(TradeFrame.id_max(), max(tradesview.id) + 1),
            )
            if tradesview
            else st.none()
        )
        sb2 = data.draw(
            st.integers(
                min_value=max(TradeFrame.id_min(), min(tradesview.id) - 1),
                max_value=min(TradeFrame.id_max(), max(tradesview.id) + 1),
            )
            if tradesview
            else st.none()
        )
        if (
            sb1 is None or sb2 is None or sb1 > sb2
        ):  # indexing on map domain with slice: integers are ordered !
            # None can be in any position in slice
            s = slice(sb2, sb1)
        else:
            s = slice(sb1, sb2)

        try:
            tfs = tradesview[s]
        except KeyError as ke:
            # the test id set from hypothesis is bound to acceptable values,
            # so if this case happen we should raise
            raise ke

        assert isinstance(tfs, TradesViewBase)
        # CAREFUL slicing seems to be inclusive both on start and stop in pandas.DataFrame
        # not like with python, but this match what we want in slicing a mapping domain
        if s.start is not None:
            if s.stop is not None:
                assert len(tfs) == len(
                    [i for i in tradesview.id if s.start <= i <= s.stop]
                ), f" len(tfs)!= len([i for i in tradesview.id if s.start <= i <= s.stop] : {len(tfs)} != len({[i for i in tradesview.id if s.start<=i<=s.stop]}"
            else:
                assert len(tfs) == len(
                    [i for i in tradesview.id if s.start <= i]
                ), f" len(tfs)!= len([i for i in tradesview.id if s.start <= i] : {len(tfs)} != len({[i for i in tradesview.id if s.start<=i]}"
        elif s.stop is not None:
            assert len(tfs) == len(
                [i for i in tradesview.id if i <= s.stop]
            ), f" len(tfs)!= len([i for i in tradesview.id if i <= s.stop] : {len(tfs)} != len({[i for i in tradesview.id if i<= s.stop]}"
        else:
            assert tfs == tradesview
            # making sure we have the usual copy behavior when taking slices
            assert tfs is not tradesview

        counter = 0
        for t in tfs:  # __iter__
            assert isinstance(t, Trade)
            assert t in tradesview  # value present in origin check
            assert tradesview[t.id] == t  # same value as origin via equality check
            counter += 1

        assert counter == len(tfs), f"counter != len(tfs) : {counter} != {len(tfs)}"

    @given(tradesview=TradesViewBase.strategy(), tradeframe_new=TradeFrame.strategy())
    def test_call(self, tradesview: TradesViewBase, tradeframe_new: TradeFrame):

        # old_df = tradeframe.df.copy(deep=True)
        # old_id = tradeframe.id

        tradesview(frame=tradeframe_new)

        # after update they are essentially "the same" (altho not '==') in this precise sense:

        # contains the same set of ids
        assert set(tradesview.id) == set(tradeframe_new.id)

        # have access to the same trades (might not be in the same order however)
        for t in tradeframe_new:
            assert t in tradesview
        for t in tradesview:
            assert t in tradesview

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

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
    def test_eq_mapping(self, ohlcview: OHLCViewBase):
        assert ohlcview == ohlcview
        # taking a copy via slice and comparing
        assert ohlcview == ohlcview[:]

    @given(ohlcview=OHLCViewBase.strategy(), data=st.data())
    def test_timeindex_mapping(self, ohlcview: OHLCViewBase, data):
        # test we can iterate on contained data, and that length matches.
        # Ref : https://docs.python.org/3/library/collections.abc.html
        tfl = len(ohlcview)  # __len__

        counter = 0
        for t in ohlcview:  # __iter__
            assert isinstance(t, PriceCandle)
            assert t in ohlcview  # __contains__
            # pick random time in the candle to retrieve the candle:
            dt = data.draw(st.datetimes(min_value=t.open_time, max_value=t.close_time))
            assert ohlcview[dt] == t  # __getitem__ on CONTINUOUS index in mapping
            counter += 1

        assert counter == tfl

        # TODO: bounding index to what (pandas optimization) can handle
        xdt = data.draw(st.datetimes())
        assume(xdt not in ohlcview)
        with self.assertRaises(KeyError) as exc:
            ohlcview[xdt]
        assert isinstance(exc.exception, KeyError)

    @given(ohlcview=OHLCViewBase.strategy(), data=st.data())
    def test_timeslice_mapping(self, ohlcview: OHLCViewBase, data):
        # test we can iterate on contained data, and that length matches.
        # Ref : https://docs.python.org/3/library/collections.abc.html

        # taking slice bounds to possibly englobe all ids, and a bit more...
        sb1 = data.draw(
            st.datetimes(
                min_value=ohlcview.open_time - timedelta(days=1),
                max_value=ohlcview.close_time + timedelta(days=1),
            )
            if ohlcview
            else st.none()
        )
        sb2 = data.draw(
            st.datetimes(
                min_value=ohlcview.open_time - timedelta(days=1),
                max_value=ohlcview.close_time + timedelta(days=1),
            )
            if ohlcview
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
            tfs = ohlcview[s]
        except KeyError as ke:
            # This may trigger, until we bound the test datetime set from hypothesis...
            self.skipTest(ke)

        assert isinstance(tfs, OHLCViewBase)
        # CAREFUL slicing seems to be inclusive both on start and stop in pandas.DataFrame
        # not like with python, but this match what we want in slicing a mapping domain
        if s.start is not None:
            if s.stop is not None:
                assert len(tfs) == len(
                    [i for i in ohlcview.frame if s.start <= i.open_time <= s.stop]
                ), f" len(tfs)!= len([i for i in ohlcview.frame if s.start <= i <= s.stop] : {len(tfs)} != len({[i for i in ohlcview.frame if s.start <= i.open_time <= s.stop]}"
            else:
                assert len(tfs) == len(
                    [i for i in ohlcview.frame if s.start <= i.open_time]
                ), f" len(tfs)!= len([i for i in ohlcview.frame if s.start <= i] : {len(tfs)} != len({[i for i in ohlcview.frame if s.start <= i.open_time]}"
        elif s.stop is not None:
            assert len(tfs) == len(
                [i for i in ohlcview.frame if i.open_time <= s.stop]
            ), f" len(tfs)!= len([i for i in ohlcview.frame if i <= s.stop] : {len(tfs)} != len({[i for i in ohlcview.frame if i.open_time <= s.stop]}"
        else:
            assert tfs == ohlcview
            # making sure we have the usual copy behavior when taking slices
            assert tfs is not ohlcview

        counter = 0
        for t in tfs:  # __iter__
            assert isinstance(t, PriceCandle)
            assert t in ohlcview  # value present in origin check
            # pick random time in the candle to retrieve the candle:
            dt = data.draw(st.datetimes(min_value=t.open_time, max_value=t.close_time))
            assert ohlcview[dt] == t  # same value as origin via equality check
            counter += 1

        assert counter == len(tfs), f"counter != len(tfs) : {counter} != {len(tfs)}"

    @given(ohlcview=OHLCViewBase.strategy(), ohlcframe_new=OHLCFrame.strategy())
    def test_call(self, ohlcview: OHLCViewBase, ohlcframe_new: OHLCFrame):

        # old_df = tradeframe.df.copy(deep=True)
        # old_id = tradeframe.id

        ohlcview(frame=ohlcframe_new)

        # after update, frames are equal
        assert ohlcview.frame == ohlcframe_new
        if len(ohlcframe_new):
            #  and properties actually change to match the new frame data
            assert ohlcview.open_time == ohlcframe_new.open_time[0]
            assert ohlcview.close_time == ohlcframe_new.close_time[-1]
        else:
            assert ohlcview.open_time is None
            assert ohlcview.close_time is None

    @given(ohlcview=OHLCViewBase.strategy())
    def test_str(self, ohlcview: OHLCViewBase):
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

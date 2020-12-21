import dataclasses
import unittest
from datetime import timedelta

import hypothesis.strategies as st
import numpy as np
import pandas as pd
from hypothesis import assume, given

from aiobinance.api.model.ohlcframe import _OHLCFrame
from aiobinance.api.model.pricecandle import PriceCandle


class TestOHLCV(unittest.TestCase):
    @given(ohlcframe=_OHLCFrame.strategy())
    def test_strategy(self, ohlcframe: _OHLCFrame):
        # listing guarantees of the instance, upon which other properties rely
        # The index is open_time, and the open_time column is gone
        assert isinstance(ohlcframe.df.index, pd.DatetimeIndex)
        assert ohlcframe.df.index.name == "open_time"
        assert "open_time" not in ohlcframe.df.columns

        # sorting index doesnt change anything => already sorted
        assert (ohlcframe.df.index.sort_values() == ohlcframe.df.index).all()

        # asserting dtypes
        assert ohlcframe.df.dtypes.to_dict() == {
            "open": np.dtype("O"),
            "high": np.dtype("O"),
            "low": np.dtype("O"),
            "close": np.dtype("O"),
            "volume": np.dtype("O"),
            "close_time": np.dtype("datetime64[ns]"),
            "qav": np.dtype("O"),
            "num_trades": np.dtype("uint64"),
            "taker_base_vol": np.dtype("O"),
            "taker_quote_vol": np.dtype("O"),
            "is_best_match": np.dtype("O"),
        }

        # TODO: more checks

    @given(ohlcframe=_OHLCFrame.strategy())
    def test_eq(self, ohlcframe: _OHLCFrame):
        assert ohlcframe == ohlcframe
        # taking a copy via slice and comparing
        assert ohlcframe == ohlcframe[:]

    @given(ohlcframe=_OHLCFrame.strategy(), data=st.data())
    def test_timeindex(self, ohlcframe: _OHLCFrame, data):
        # test we can iterate on contained data, and that length matches.
        # Ref : https://docs.python.org/3/library/collections.abc.html
        tfl = len(ohlcframe)  # __len__

        counter = 0
        for t in ohlcframe:  # __iter__
            assert isinstance(t, PriceCandle)
            assert t in ohlcframe  # __contains__
            # pick random time in the candle to retrieve the candle:
            dt = data.draw(st.datetimes(min_value=t.open_time, max_value=t.close_time))
            assert ohlcframe[dt] == t  # __getitem__ on CONTINUOUS index in mapping
            counter += 1

        assert counter == tfl

        # TODO: bounding index to what (pandas optimization) can handle
        xdt = data.draw(st.datetimes())
        assume(xdt not in ohlcframe)
        with self.assertRaises(KeyError) as exc:
            ohlcframe[xdt]
        assert isinstance(exc.exception, KeyError)

    @given(ohlcframe=_OHLCFrame.strategy(), data=st.data())
    def test_timeslice(self, ohlcframe: _OHLCFrame, data):
        # test we can iterate on contained data, and that length matches.
        # Ref : https://docs.python.org/3/library/collections.abc.html

        # taking slice bounds to possibly englobe all ids, and a bit more...
        # but be careful with pandas timestamp bounds !
        sb1 = data.draw(
            st.datetimes(
                min_value=max(
                    ohlcframe.open_time - timedelta(days=1), pd.Timestamp.min
                ),
                max_value=min(
                    ohlcframe.close_time + timedelta(days=1), pd.Timestamp.max
                ),
            )
            if ohlcframe
            else st.none()
        )
        sb2 = data.draw(
            st.datetimes(
                min_value=max(
                    ohlcframe.open_time - timedelta(days=1), pd.Timestamp.min
                ),
                max_value=min(
                    ohlcframe.close_time + timedelta(days=1), pd.Timestamp.max
                ),
            )
            if ohlcframe
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
            tfs = ohlcframe[s]
        except KeyError as ke:
            # This may trigger, until we bound the test datetime set from hypothesis...
            self.skipTest(ke)

        assert isinstance(tfs, _OHLCFrame)
        # CAREFUL slicing seems to be inclusive both on start and stop in pandas.DataFrame
        # not like with python, but this match what we want in slicing a mapping domain
        if s.start is not None:
            if s.stop is not None:
                assert len(tfs) == len(
                    [i for i in ohlcframe if s.start <= i.open_time <= s.stop]
                ), f" len(tfs)!= len([i for i in ohlcframe if s.start <= i <= s.stop] : {len(tfs)} != len({[i for i in ohlcframe if s.start <= i.open_time <= s.stop]}"
            else:
                assert len(tfs) == len(
                    [i for i in ohlcframe if s.start <= i.open_time]
                ), f" len(tfs)!= len([i for i in ohlcframe if s.start <= i] : {len(tfs)} != len({[i for i in ohlcframe if s.start <= i.open_time]}"
        elif s.stop is not None:
            assert len(tfs) == len(
                [i for i in ohlcframe if i.open_time <= s.stop]
            ), f" len(tfs)!= len([i for i in ohlcframe if i <= s.stop] : {len(tfs)} != len({[i for i in ohlcframe if i.open_time <= s.stop]}"
        else:
            assert tfs == ohlcframe
            # making sure we have the usual copy behavior when taking slices
            assert tfs is not ohlcframe

        counter = 0
        for t in tfs:  # __iter__
            assert isinstance(t, PriceCandle)
            assert t in ohlcframe  # value present in origin check
            # pick random time in the candle to retrieve the candle:
            dt = data.draw(st.datetimes(min_value=t.open_time, max_value=t.close_time))
            assert ohlcframe[dt] == t  # same value as origin via equality check
            counter += 1

        assert counter == len(tfs), f"counter != len(tfs) : {counter} != {len(tfs)}"

    @given(tf1=_OHLCFrame.strategy(), tf2=_OHLCFrame.strategy())
    def test_intersection(self, tf1, tf2):

        tfi = tf1.intersection(tf2)

        # special case where one of them is empty
        if len(tf2) == 0:
            assert tfi == tf2
            assert tfi is not tf2
        if len(tf1) == 0:
            assert tfi == tf1
            assert tfi is not tf1

        for t in tfi:
            assert t in tf1
            assert t in tf2

    @given(tf1=_OHLCFrame.strategy(), tf2=_OHLCFrame.strategy())
    def test_merge(self, tf1, tf2):

        tfr = tf1.merge(tf2)

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

        for t in tfr:
            assert isinstance(t, PriceCandle)
            # grab original candles
            c2 = c1 = None
            if t.open_time in tf1:
                c1 = tf1[t.open_time]
            if t.open_time in tf2:
                c2 = tf2[t.open_time]

            # test logic in merging
            #  we need to pick either c1 or c2... problem is how we chose...
            if c1 is None and c2 is not None:
                assert t == c2
            elif c2 is None and c1 is not None:
                assert t == c1
            elif c1 is not None and c2 is not None:
                assert t.num_trades == max(c1.num_trades, c2.num_trades)
                if c1.num_trades > c2.num_trades:
                    assert t == c1
                elif c1.num_trades < c2.num_trades:
                    assert t == c2
                else:
                    assert t.volume == max(c1.volume, c2.volume)
                    if c1.volume > c2.volume:
                        assert t == c1
                    elif c1.volume < c2.volume:
                        assert t == c2
                    else:
                        assert t.high == max(c1.high, c2.high)
                        assert t.low == min(c1.low, c2.low)
                        # careful with strictness on bounds here,
                        # it should not prevent picking a better bound on the other side...
                        if (c1.high > c2.high and c1.low <= c2.low) or (
                            c1.high >= c2.high and c1.low < c2.low
                        ):
                            assert t == c1
                        elif (c1.high < c2.high and c1.low >= c2.low) or (
                            c1.high <= c2.high and c1.low > c2.low
                        ):
                            assert t == c2
                        else:
                            assert t == c1

            else:  # if c1 is None and c2 is None:
                self.fail("what ?")

    @given(tf1=_OHLCFrame.strategy(), tf2=_OHLCFrame.strategy())
    def test_difference(self, tf1: _OHLCFrame, tf2: _OHLCFrame):

        tfr = tf2.difference(tf1)

        # special case where tf1 is empty
        if len(tf1) == 0:
            assert tfr == tf2
            assert (
                tfr is not tf2
            )  # we get a copy, not the same frame ( in case it gets modified somehow...)

        # len(tf2) is a max len for the resulting frame
        assert len(tfr) <= len(tf2)

        # result is only made up of tf2 candles if they are not in tf1
        for t in tf2:
            assert isinstance(t, PriceCandle)
            if t in tf1:
                assert t not in tfr
            else:
                assert t in tfr

        # in any case tf1 candles are not in resulting frame
        for t in tf1:
            assert isinstance(t, PriceCandle)
            assert t not in tfr

    @given(ohlcv=_OHLCFrame.strategy())
    def test_str(self, ohlcv: _OHLCFrame):
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

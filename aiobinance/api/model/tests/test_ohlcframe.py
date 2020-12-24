import dataclasses
import unittest
from datetime import timedelta, timezone

import hypothesis.strategies as st
import pandas as pd
from hypothesis import HealthCheck, assume, given, reproduce_failure, settings

from aiobinance.api.model.ohlcframe import OHLCFrame
from aiobinance.api.model.pricecandle import PriceCandle

# TMP : to temporary help us verify frame structure
# TODO : do it in hte type itself somehow...
OHLCFrameColumns = [
    "open_time",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "close_time",
    "qav",
    "num_trades",
    "taker_base_vol",
    "taker_quote_vol",
    "is_best_match",
]


def assert_columns(ohlcframe):
    # Order matters here...
    assert (
        [ohlcframe.df.index.name] if not ohlcframe.df.empty else []
    ) + ohlcframe.df.columns.to_list() == OHLCFrameColumns


class TestOHLCFrame(unittest.TestCase):
    @given(ohlcframe=OHLCFrame.strategy())
    def test_strategy(self, ohlcframe: OHLCFrame):
        # empty is a special se in pandas behavior...
        if ohlcframe.df.empty:
            assert_columns(ohlcframe)
        else:
            assert_columns(ohlcframe)
            assert ohlcframe.df.index.name == "open_time"
            assert isinstance(ohlcframe.df.index, pd.DatetimeIndex)
            assert ohlcframe.df.index.tz is None

        # assert reflexive equality in all cases
        assert ohlcframe == ohlcframe

    @given(ohlcframe=OHLCFrame.strategy())
    def test_eq(self, ohlcframe: OHLCFrame):
        assert ohlcframe == ohlcframe
        # taking a copy via slice and comparing
        assert ohlcframe == ohlcframe[:]

    @given(ohlcframe=OHLCFrame.strategy(), data=st.data())
    def test_timeindex(self, ohlcframe: OHLCFrame, data):
        # test we can iterate on contained data, and that length matches.
        # Ref : https://docs.python.org/3/library/collections.abc.html
        tfl = len(ohlcframe)  # __len__

        counter = 0
        for t in ohlcframe:  # __iter__
            assert isinstance(t, PriceCandle)
            assert t in ohlcframe  # __contains__
            # pick random time in the candle to retrieve the candle:
            dt = data.draw(
                st.datetimes(
                    min_value=t.open_time.replace(tzinfo=None),
                    max_value=t.close_time.replace(tzinfo=None),
                )
            )

            # __getitem__ on CONTINUOUS index in mapping
            retrieve = ohlcframe[dt]
            if isinstance(retrieve, PriceCandle):
                assert t == retrieve
            # CAREFUL we could retrieve two candles (if overlap - allowed by strategy)
            elif isinstance(retrieve, OHLCFrame):
                assert t in retrieve
            else:
                self.fail(f"__getitem__ returns not in [{PriceCandle},{OHLCFrame}]")
            counter += 1

        assert counter == tfl

        # TODO: bounding index to what pandas optimization can handle
        xdt = data.draw(st.datetimes())
        assume(xdt not in ohlcframe)
        with self.assertRaises(KeyError) as exc:
            ohlcframe[xdt]
        assert isinstance(exc.exception, KeyError)

    @given(ohlcframe=OHLCFrame.strategy(), data=st.data())
    def test_timeslice(self, ohlcframe: OHLCFrame, data):
        # test we can iterate on contained data, and that length matches.
        # Ref : https://docs.python.org/3/library/collections.abc.html

        # taking slice bounds to possibly englobe all ids, and a bit more...
        # but be careful with pandas timestamp bounds !
        sb1 = data.draw(
            st.datetimes(
                min_value=max(
                    ohlcframe.open_time.replace(tzinfo=None) - timedelta(days=1),
                    pd.Timestamp.min.to_pydatetime(),
                ),
                max_value=min(
                    ohlcframe.close_time.replace(tzinfo=None) + timedelta(days=1),
                    pd.Timestamp.max.to_pydatetime(),
                ),
                timezones=st.just(
                    timezone.utc
                ),  # because we will do tz-aware comparison
            )
            if ohlcframe
            else st.none()
        )
        sb2 = data.draw(
            st.datetimes(
                min_value=max(
                    ohlcframe.open_time.replace(tzinfo=None) - timedelta(days=1),
                    pd.Timestamp.min.to_pydatetime(),
                ),
                max_value=min(
                    ohlcframe.close_time.replace(tzinfo=None) + timedelta(days=1),
                    pd.Timestamp.max.to_pydatetime(),
                ),
                timezones=st.just(
                    timezone.utc
                ),  # because we will do tz-aware comparison
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

        if ohlcframe.empty:  # empty case : result is also empty
            assert ohlcframe[s] == ohlcframe
        elif (s.start is None or s.start <= ohlcframe.open_time) and (
            s.stop is None or s.stop >= ohlcframe.close_time
        ):  # larger slice => all included
            assert ohlcframe[s] == ohlcframe
        else:
            try:
                tfs = ohlcframe[s]
            except KeyError as ke:
                # This may trigger, until we bound the test datetime set from hypothesis...
                # self.skipTest(ke)
                raise ke

            assert isinstance(tfs, OHLCFrame)
            # CAREFUL slicing seems to be inclusive both on start and stop in pandas.DataFrame
            # not like with python, but this match what we want in slicing a mapping domain
            if s.start is not None:
                if s.stop is not None:
                    assert len(tfs) == len(
                        [
                            i
                            for i in ohlcframe
                            if s.start <= i.close_time and i.open_time <= s.stop
                        ]
                    ), f"{len(tfs)} != len({[i for i in ohlcframe if s.start <= i.close_time and i.open_time <= s.stop]}"
                else:
                    assert len(tfs) == len(
                        [i for i in ohlcframe if s.start <= i.close_time]
                    ), f"{len(tfs)} != len({[i for i in ohlcframe if s.start <= i.close_time]}"
            elif s.stop is not None:
                assert len(tfs) == len(
                    [i for i in ohlcframe if i.open_time <= s.stop]
                ), f"{len(tfs)} != len({[i for i in ohlcframe if i.open_time <= s.stop]}"
            else:
                assert tfs == ohlcframe
                # making sure we have the usual copy behavior when taking slices
                assert tfs is not ohlcframe

            counter = 0
            for t in tfs:  # __iter__
                assert isinstance(t, PriceCandle)
                assert t in ohlcframe  # value present in origin check
                # pick random time in the candle to retrieve the candle:
                dt = data.draw(
                    st.datetimes(
                        min_value=t.open_time.replace(tzinfo=None),
                        max_value=t.close_time.replace(tzinfo=None),
                    )
                )
                assert ohlcframe[dt] == t  # same value as origin via equality check
                counter += 1

            assert counter == len(tfs), f"counter != len(tfs) : {counter} != {len(tfs)}"

    @given(tf1=OHLCFrame.strategy(), tf2=OHLCFrame.strategy())
    @settings(
        suppress_health_check=[HealthCheck.too_slow]
    )  # TODO : improve strategy... and maybe test as well ?
    def test_intersection(self, tf1, tf2):
        # intersect with self is self
        assert tf1.intersection(tf1) == tf1

        itf1 = tf1.intersection(tf2)

        # verifying shape after operation
        assert_columns(itf1)

        for c in itf1:
            assert c in tf1
            assert c in tf2

        itf2 = tf2.intersection(tf1)
        # verifying shape after operation
        assert_columns(itf2)
        assert itf1 == itf2

    @given(tf1=OHLCFrame.strategy(), tf2=OHLCFrame.strategy())
    @settings(
        suppress_health_check=[HealthCheck.too_slow]
    )  # TODO : improve strategy... and maybe test as well ?
    def test_union(self, tf1, tf2):
        # union with self is self
        assert tf1.union(tf1) == tf1

        def better_candle(other_tf: OHLCFrame, c: PriceCandle):
            # assert we had a "better" candle in the other
            try:
                oc = other_tf[c.open_time]
            except KeyError:
                return False
            else:
                # Here, for merging, we need a precise indexing on opentime, not the continuous one...
                if isinstance(oc, PriceCandle) and oc.open_time == c.open_time:
                    # TODO : this can be simplified if we separate the various parts of the candle...
                    return (
                        oc.num_trades > c.num_trades
                        or oc.volume > c.volume
                        or (
                            (oc.high >= c.high and oc.low < c.low)
                            or (oc.high > c.high and oc.low <= c.low)
                        )
                    )
                elif isinstance(oc, OHLCFrame):
                    # if there was multiple candidates, there is at least one better.
                    for oci in oc:
                        # Precise open_time matching for merging...
                        if (oci.open_time == c.open_time) and (
                            # TODO Note we could rely here on the fact that OHLC quacks a bit like a candle...
                            oci.num_trades > c.num_trades
                            or oci.volume > c.volume
                            or (
                                (oci.high >= c.high and oci.low < c.low)
                                or (oci.high > c.high and oci.low <= c.low)
                            )
                        ):
                            return True
                        # other my be better or worse, we only need one better

                    return False  # No better candle has been found

        utf1 = tf1.union(tf2)

        # verifying shape after operation
        assert_columns(utf1)

        # REMINDER: the union actually merges, so the relationship is not trivial:
        for c in tf1:
            if better_candle(  # Note : None result is also interpreted as False
                other_tf=tf2, c=c
            ):  # if tf2 has a better candle, c is not in union
                assert c not in utf1
            else:
                assert c in utf1

        # Not symmetric ! the left of the union is privileged when candle not explicitly "better"

        utf2 = tf2.union(tf1)
        # verifying shape after operation
        assert_columns(utf2)

        # REMINDER: the union actually merges, so the relationship is not trivial:
        for c in tf2:
            if better_candle(  # Note : None result is also interpreted as False
                other_tf=tf1, c=c
            ):  # if tf1 has a better candle, c is not in union
                assert c not in utf2
            else:
                assert c in utf2

        # Note : this might not be true ! (candle can have "unchecked values" different in utf1 and in utf2)
        # But if there is ambiguity, existing data (left, self) prevails.
        # assert utf1 == utf2

    @given(tf1=OHLCFrame.strategy(), tf2=OHLCFrame.strategy())
    @settings(
        suppress_health_check=[HealthCheck.too_slow]
    )  # TODO : improve strategy... and maybe test as well ?
    def test_difference(self, tf1, tf2):

        # difference with self is empty
        assert tf1.difference(tf1).empty

        dtf1 = tf1.difference(tf2)

        # verifying shape after operation
        assert_columns(dtf1)

        for c in dtf1:
            assert c in tf1
            assert c not in tf2

        for c in tf1:
            if c not in tf2:
                assert c in dtf1

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

import dataclasses
import unittest
from datetime import timedelta, timezone

import hypothesis.strategies as st
import pandas as pd
from hypothesis import HealthCheck, assume, given, settings

from aiobinance.api.model.trade import Trade
from aiobinance.api.model.tradeframe import TradeFrame

# TMP : to temporary help us verify frame structure
# TODO : do it in hte type itself somehow...
TradeFrameColumns = [
    "id",
    "time_utc",
    "symbol",
    "price",
    "qty",
    "quote_qty",
    "commission",
    "commission_asset",
    "is_buyer",
    "is_maker",
    "order_id",
    "order_list_id",
    "is_best_match",
]


def assert_columns(tradeframe):
    # Order matters here...
    assert (
        [tradeframe.df.index.name] if not tradeframe.df.empty else []
    ) + tradeframe.df.columns.to_list() == TradeFrameColumns


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
        # careful with empty dataframe special case...
        df = tf.df if tf.df.empty else tf.df.reset_index(drop=False)
        # careful : pandas may optimize these...
        for fdt, cdt in zip(df.dtypes.items(), Trade.as_dtype().items()):
            assert fdt[0] == cdt[0]
            # dtype should be same or provide safe conversion
            assert fdt[1] == cdt[1] or fdt[1] < cdt[1]

    @given(tradeframe=TradeFrame.strategy())
    def test_eq_mapping(self, tradeframe: TradeFrame):
        assert tradeframe == tradeframe
        # taking a copy via slice and comparing
        assert tradeframe == tradeframe[:]

    @given(tradeframe=TradeFrame.strategy(), data=st.data())
    def test_index_id_mapping(self, tradeframe: TradeFrame, data):
        # test we can iterate on contained data, and that length matches.
        # Ref : https://docs.python.org/3/library/collections.abc.html
        tfl = len(tradeframe)  # __len__

        counter = 0
        for t in tradeframe:  # __iter__
            assert isinstance(t, Trade)
            assert t in tradeframe  # __contains__
            assert tradeframe[t.id] == t  # __getitem__ on index in mapping
            counter += 1

        assert counter == tfl

        # TODO: bounding index to what C long (pandas optimization) can handle
        rid = data.draw(st.integers())
        assume(rid not in tradeframe.id)
        with self.assertRaises(KeyError) as exc:
            tradeframe[rid]
        assert isinstance(exc.exception, KeyError)

    @given(tradeframe=TradeFrame.strategy(), data=st.data())
    def test_index_time_mapping(self, tradeframe: TradeFrame, data):
        # test we can iterate on contained data, and that length matches.
        # Ref : https://docs.python.org/3/library/collections.abc.html
        tfl = len(tradeframe)  # __len__

        counter = 0
        for t in tradeframe:  # __iter__
            assert isinstance(t, Trade)
            assert t in tradeframe  # __contains__
            if isinstance(tradeframe[t.time_utc], TradeFrame):
                assert (
                    t in tradeframe[t.time_utc]
                )  # we may have multiple trades with the dame time_utc
            else:  # is a Trade
                assert (
                    tradeframe[t.time_utc] == t
                )  # same value as origin via equality check
            counter += 1

        assert counter == tfl

        # TODO: bounding index to what C long (pandas optimization) can handle
        rtime_utc = data.draw(
            st.datetimes(
                min_value=pd.Timestamp.min.to_pydatetime(),
                max_value=pd.Timestamp.max.to_pydatetime(),
            )
        )
        assume(rtime_utc not in tradeframe.time_utc)
        with self.assertRaises(KeyError) as exc:
            tradeframe[rtime_utc]
        assert isinstance(exc.exception, KeyError)

    @given(tradeframe=TradeFrame.strategy(), data=st.data())
    def test_index_symbol_mapping(self, tradeframe: TradeFrame, data):
        # test we can iterate on contained data, and that length matches.
        # Ref : https://docs.python.org/3/library/collections.abc.html

        slist = tradeframe.symbol
        for s in slist:
            subframe = tradeframe[s]
            assert isinstance(subframe, TradeFrame)
            for t in subframe:
                assert t in tradeframe
            for t in tradeframe:
                if t.symbol == s:
                    assert t in subframe

    @given(tradeframe=TradeFrame.strategy(), data=st.data())
    def test_slice_id_mapping(self, tradeframe: TradeFrame, data):
        # test we can iterate on contained data, and that length matches.
        # Ref : https://docs.python.org/3/library/collections.abc.html

        # taking slice bounds to possibly englobe all ids, and a bit more...
        sb1 = data.draw(
            st.integers(
                min_value=max(TradeFrame.id_min(), min(tradeframe.id) - 1),
                max_value=min(TradeFrame.id_max(), max(tradeframe.id) + 1),
            )
            if tradeframe
            else st.none()
        )
        sb2 = data.draw(
            st.integers(
                min_value=max(TradeFrame.id_min(), min(tradeframe.id) - 1),
                max_value=min(TradeFrame.id_max(), max(tradeframe.id) + 1),
            )
            if tradeframe
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
            tfs = tradeframe[s]
        except KeyError as ke:
            # the test id set from hypothesis is bound to acceptable values,
            # so if this case happen we should raise
            raise ke

        assert isinstance(tfs, TradeFrame)
        # CAREFUL slicing seems to be inclusive both on start and stop in pandas.DataFrame
        # not like with python, but this match what we want in slicing a mapping domain
        if s.start is not None:
            if s.stop is not None:
                assert len(tfs) == len(
                    [i for i in tradeframe.id if s.start <= i <= s.stop]
                ), f" len(tfs)!= len([i for i in tradeframe.id if s.start <= i <= s.stop] : {len(tfs)} != len({[i for i in tradeframe.id if s.start<=i<=s.stop]}"
            else:
                assert len(tfs) == len(
                    [i for i in tradeframe.id if s.start <= i]
                ), f" len(tfs)!= len([i for i in tradesview.id if s.start <= i] : {len(tfs)} != len({[i for i in tradeframe.id if s.start<=i]}"
        elif s.stop is not None:
            assert len(tfs) == len(
                [i for i in tradeframe.id if i <= s.stop]
            ), f" len(tfs)!= len([i for i in tradesview.id if i <= s.stop] : {len(tfs)} != len({[i for i in tradeframe.id if i<= s.stop]}"
        else:
            assert tfs == tradeframe
            # making sure we have the usual copy behavior when taking slices
            assert tfs is not tradeframe

        counter = 0
        for t in tfs:  # __iter__
            assert isinstance(t, Trade)
            assert t in tradeframe  # value present in origin check
            assert tradeframe[t.id] == t  # same value as origin via equality check
            counter += 1

        assert counter == len(tfs), f"counter != len(tfs) : {counter} != {len(tfs)}"

    @given(tradeframe=TradeFrame.strategy(), data=st.data())
    # @reproduce_failure('5.49.0', b'AXicY2QgBzASLUgUAAABkwAE')
    def test_slice_time_mapping(self, tradeframe: TradeFrame, data):
        # test we can iterate on contained data, and that length matches.
        # Ref : https://docs.python.org/3/library/collections.abc.html

        # taking slice bounds to possibly englobe all ids, and a bit more...
        # but be careful with pandas timestamp bounds !
        sb1 = data.draw(
            st.datetimes(
                min_value=pd.Timestamp.min.to_pydatetime(),
                max_value=pd.Timestamp.max.to_pydatetime(),
                timezones=st.just(
                    timezone.utc
                ),  # because we will do tz-aware comparison
            )
            if tradeframe
            else st.none()
        )
        sb2 = data.draw(
            st.datetimes(
                min_value=pd.Timestamp.min.to_pydatetime(),
                max_value=pd.Timestamp.max.to_pydatetime(),
                timezones=st.just(
                    timezone.utc
                ),  # because we will do tz-aware comparison
            )
            if tradeframe
            else st.none()
        )
        if (
            sb1 is None or sb2 is None or sb1 > sb2
        ):  # indexing on map domain with slice: integers are ordered !
            # None can be in any position in slice
            s = slice(sb2, sb1)
        else:
            s = slice(sb1, sb2)

        if tradeframe.empty:  # empty case : result is also empty
            assert tradeframe[s] == tradeframe
        else:
            try:
                tfs = tradeframe[s]
            except KeyError as ke:
                # This may trigger, until we bound the test datetime set from hypothesis...
                # self.skipTest(ke)
                raise ke

            assert isinstance(tfs, TradeFrame)
            # CAREFUL slicing seems to be inclusive both on start and stop in pandas.DataFrame
            # not like with python, but this match what we want in slicing a mapping domain
            if s.start is not None:
                if s.stop is not None:
                    assert len(tfs) == len(
                        [i for i in tradeframe if s.start <= i.time_utc <= s.stop]
                    ), f"{len(tfs)} != len({[i for i in tradeframe if s.start <= i.time_utc <= s.stop]}"
                else:
                    assert len(tfs) == len(
                        [i for i in tradeframe if s.start <= i.time_utc]
                    ), f"{len(tfs)} != len({[i for i in tradeframe if s.start <= i.time_utc]}"
            elif s.stop is not None:
                assert len(tfs) == len(
                    [i for i in tradeframe if i.time_utc <= s.stop]
                ), f"{len(tfs)} != len({[i for i in tradeframe if i.time_utc <= s.stop]}"
            else:
                assert tfs == tradeframe
                # making sure we have the usual copy behavior when taking slices
                assert tfs is not tradeframe

            counter = 0
            for t in tfs:  # __iter__
                assert isinstance(t, Trade)
                assert t in tradeframe  # value present in origin check
                if isinstance(tradeframe[t.time_utc], TradeFrame):
                    assert (
                        t in tradeframe[t.time_utc]
                    )  # we may have multiple trades with the dame time_utc
                else:  # is a Trade
                    assert (
                        tradeframe[t.time_utc] == t
                    )  # same value as origin via equality check
                counter += 1

            assert counter == len(tfs), f"counter != len(tfs) : {counter} != {len(tfs)}"

    @given(tf1=TradeFrame.strategy(), tf2=TradeFrame.strategy())
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

    @given(tf1=TradeFrame.strategy(), tf2=TradeFrame.strategy())
    @settings(
        suppress_health_check=[HealthCheck.too_slow]
    )  # TODO : improve strategy (optimize + unique ids)... and maybe test as well ?
    def test_union(self, tf1, tf2):
        # union with self is self
        assert tf1.union(tf1) == tf1

        utf1 = tf1.union(tf2)

        # verifying shape after operation
        assert_columns(utf1)

        # REMINDER: the union on trade does do merge on id, and priority is given to self
        # but nothing else (like for OHLCFrame), so here the relationship is trivial
        for c in tf1:
            assert c in utf1

        for t in tf2:
            if t.id not in tf1:
                assert t in utf1
            else:  # if t.id in tf1, the original should be there, the new one is lost
                # It is not a problem in our usecase since binance id are specified to be unique
                assert tf1[t.id] in utf1
                # TODO : maybe we should raise on this ??

        utf2 = tf2.union(tf1)

        # verifying shape after operation
        assert_columns(utf2)

        # REMINDER: the union on trade does do merge on id, and priority is given to self
        # but nothing else (like for OHLCFrame), so here the relationship is trivial
        for c in tf2:
            assert c in utf2

        for t in tf1:
            if t.id not in tf2:
                assert t in utf2
            else:  # if t.id in tf1, the original should be there, the new one is lost
                # It is not a problem in our usecase since binance id are specified to be unique
                assert tf2[t.id] in utf2
                # TODO : maybe we should raise on this ??

    @given(tf1=TradeFrame.strategy(), tf2=TradeFrame.strategy())
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

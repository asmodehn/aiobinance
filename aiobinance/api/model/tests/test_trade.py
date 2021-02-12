import dataclasses
import unittest
from datetime import datetime, timedelta, timezone

import hypothesis.strategies as st
import numpy as np
import pandas as pd
from hypothesis import HealthCheck, given, settings
from pydantic import ValidationError

from aiobinance.api.model.trade import Trade


class TestTrade(unittest.TestCase):
    @given(trade=Trade.strategy())
    def test_strategy_dtypes(self, trade: Trade):
        # TODO : test min / max values
        arraylike = [tuple(dataclasses.asdict(trade).values())]
        npa = np.array(arraylike, dtype=list(Trade.as_dtype().items()))

        try:
            # confirm we do not loose any information by converting types and storing into a structured array
            stored_trade = Trade(
                **{f.name: v for f, v in zip(dataclasses.fields(Trade), npa[0])}
            )
        except ValidationError:
            raise
        assert stored_trade == trade

    @given(
        dt=st.datetimes(
            min_value=pd.Timestamp.min.to_pydatetime(),
            max_value=pd.Timestamp.max.to_pydatetime(),
            timezones=st.none(),
        )
    )  # naive datetimes here: we are not testing timezone conversion.
    # @settings(suppress_health_check=[HealthCheck.too_slow])
    def test_convert_time(self, dt: datetime):
        # forcing naive datetime to be utc-aware
        py_dt = Trade.convert_pandas_timestamp(dt)
        for f in ["year", "month", "day", "hour", "minute", "second", "microsecond"]:
            assert getattr(dt, f) == getattr(py_dt, f)  # same data
        assert py_dt.tzinfo == timezone.utc  # now UTC timezone

        # check with python timestamp
        # NOTE : default [us] is IMPRECISE ! converting to/from timestamp seems to error on float precision...
        py_ts = py_dt.timestamp()
        # Therefore we assert on microsecond delta only...
        converted = Trade.convert_pandas_timestamp(py_ts)  # expected [ns] timestamp
        assert py_dt - converted < timedelta(milliseconds=1)

        # check as a pandas timestamp
        ts = pd.Timestamp(dt)
        converted = Trade.convert_pandas_timestamp(ts)
        assert py_dt == converted, f"{py_dt} != {converted}"

        # REMINDER : Deprecated since version 1.11.0: NumPy does not store timezone information.
        np_dt = np.datetime64(dt)
        converted = Trade.convert_pandas_timestamp(np_dt)
        assert py_dt == converted, f"{py_dt} != {converted}"

    @given(trade=Trade.strategy())
    def test_str(self, trade: Trade):
        # Check sensible information is displayed (order doesnt matter for output to human)
        trade_str = str(trade)
        assert f"time_utc: {str(trade.time_utc)}" in trade_str
        assert f"symbol: {str(trade.symbol)}" in trade_str
        assert f"id: {str(trade.id)}" in trade_str
        assert f"price: {str(trade.price)}" in trade_str
        assert f"qty: {str(trade.qty)}" in trade_str
        assert f"quote_qty: {str(trade.quote_qty)}" in trade_str
        assert f"commission: {str(trade.commission)}" in trade_str
        assert f"commission_asset: {str(trade.commission_asset)}" in trade_str
        assert f"is_buyer: {str(trade.is_buyer)}" in trade_str
        assert f"is_maker: {str(trade.is_maker)}" in trade_str
        assert f"order_id: {str(trade.order_id)}" in trade_str
        assert f"order_list_id: {str(trade.order_list_id)}" in trade_str
        assert f"is_best_match: {str(trade.is_best_match)}" in trade_str

    @given(trade=Trade.strategy())
    def test_dir(self, trade: Trade):
        # check all information is exposed
        expected = {
            "time_utc",
            "symbol",
            "id",
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
        }
        assert {a for a in dir(trade)}.issuperset(expected), expected.difference(
            {a for a in dir(trade)}
        )

        # check no extra information is exposed
        assert {a for a in dir(trade) if not a.startswith("__")}.issubset(expected), {
            a for a in dir(trade) if not a.startswith("__")
        }.difference(expected)


if __name__ == "__main__":
    unittest.main()

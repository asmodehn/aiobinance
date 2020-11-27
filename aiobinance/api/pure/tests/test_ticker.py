import unittest

from hypothesis import given

from aiobinance.api.pure.ticker import Ticker, st_ticker


class TestTicker(unittest.TestCase):
    @given(ticker=st_ticker())
    def test_str(self, ticker):
        # Check sensible information is displayed
        tkrstr = str(ticker)
        assert f"symbol: {ticker.symbol}" in tkrstr
        assert f"price_change: {ticker.price_change}" in tkrstr
        assert f"price_change_percent: {ticker.price_change_percent}" in tkrstr
        assert f"weighted_avg_price: {ticker.weighted_avg_price}" in tkrstr
        assert f"prev_close_price: {ticker.prev_close_price}" in tkrstr
        assert f"last_price: {ticker.last_price}" in tkrstr
        assert f"last_qty: {ticker.last_qty}" in tkrstr
        assert f"bid_price: {ticker.bid_price}" in tkrstr
        assert f"ask_price: {ticker.ask_price}" in tkrstr
        assert f"open_price: {ticker.open_price}" in tkrstr
        assert f"high_price: {ticker.high_price}" in tkrstr
        assert f"low_price: {ticker.low_price}" in tkrstr
        assert f"volume: {ticker.volume}" in tkrstr
        assert f"quote_volume: {ticker.quote_volume}" in tkrstr
        assert f"open_time: {ticker.open_time}" in tkrstr
        assert f"close_time: {ticker.close_time}" in tkrstr
        assert f"first_id: {ticker.first_id}" in tkrstr
        assert f"last_id: {ticker.last_id}" in tkrstr
        assert f"count: {ticker.count}" in tkrstr

    @given(ticker=st_ticker())
    def test_dir(self, ticker: Ticker):
        # check all information is exposed
        assert {a for a in dir(ticker)}.issuperset(
            {
                "symbol",
                "price_change",
                "price_change_percent",
                "weighted_avg_price",
                "prev_close_price",
                "last_price",
                "last_qty",
                "bid_price",
                "ask_price",
                "open_price",
                "high_price",
                "low_price",
                "volume",
                "quote_volume",
                "open_time",
                "close_time",
                "first_id",
                "last_id",
                "count",
            }
        )

        # check no extra information is exposed
        assert {a for a in dir(ticker) if not a.startswith("__")}.issubset(
            {
                "symbol",
                "price_change",
                "price_change_percent",
                "weighted_avg_price",
                "prev_close_price",
                "last_price",
                "last_qty",
                "bid_price",
                "ask_price",
                "open_price",
                "high_price",
                "low_price",
                "volume",
                "quote_volume",
                "open_time",
                "close_time",
                "first_id",
                "last_id",
                "count",
            }
        )

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from aiobinance.api.exchange import Exchange
from aiobinance.api.model.ohlcframe import PriceCandle
from aiobinance.api.ohlcview import OHLCView
from aiobinance.api.rawapi import Binance


@pytest.mark.asyncio
@pytest.mark.vcr
async def test_price_from_binance():
    """ get binance price"""

    start_time = datetime.fromtimestamp(1598524340551 / 1000, tz=timezone.utc)
    end_time = start_time + timedelta(days=1)

    api = Binance()  # we dont need private requests here
    # Ref : https://binance-docs.github.io/apidocs/spot/en/#kline-candlestick-data

    exchange = Exchange(api=api, test=True)

    await exchange()  # need to retrieve markets

    ohlcv = exchange.markets["COTIBNB"].price

    assert isinstance(ohlcv, OHLCView)

    # actually get data
    await ohlcv(start_time=start_time, stop_time=end_time, interval="3m")

    assert len(ohlcv) == 480
    for c in ohlcv:
        assert isinstance(c, PriceCandle)

    first = ohlcv.frame[0]
    assert first.open_time == datetime(
        year=2020, month=8, day=27, hour=10, minute=33, tzinfo=timezone.utc
    )
    assert first.open == Decimal("0.00320100")
    assert first.high == Decimal("0.00322600")
    assert first.low == Decimal("0.00320100")
    assert first.close == Decimal("0.00322600")
    assert first.volume == Decimal("7705.00000000")
    assert first.close_time == datetime(
        year=2020,
        month=8,
        day=27,
        hour=10,
        minute=35,
        second=59,
        microsecond=999000,
        tzinfo=timezone.utc,
    )
    assert first.qav == Decimal("24.66804700")
    assert first.num_trades == 5
    assert first.taker_base_vol == Decimal("176.00000000")
    assert first.taker_quote_vol == Decimal("0.56771800")
    assert first.is_best_match == 0  # ??


if __name__ == "__main__":
    pytest.main(["-s", __file__, "--block-network"])
    # record run
    # pytest.main(['-s', __file__, '--with-keyfile', '--record-mode=new_episodes'])

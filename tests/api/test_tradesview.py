from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from aiobinance.api.exchange import Exchange
from aiobinance.api.model.trade import Trade
from aiobinance.api.rawapi import Binance
from aiobinance.api.tradesview import TradesView


@pytest.mark.asyncio
@pytest.mark.vcr(
    filter_headers=["X-MBX-APIKEY"], filter_query_parameters=["timestamp", "signature"]
)
async def test_trades_from_binance(keyfile):
    """ get binance balances"""

    start_time = datetime.fromtimestamp(1598524340551 / 1000, tz=timezone.utc)
    end_time = start_time + timedelta(days=1)

    api = Binance(credentials=keyfile)  # we need private requests here !

    exchange = Exchange(api=api)

    await exchange()  # to retrieve data

    trades = exchange.markets["COTIBNB"].trades

    assert isinstance(trades, TradesView)

    # updating known trades list (if necessary)
    await trades.at(start_time=start_time, stop_time=end_time)

    assert len(trades) == 17
    for t in trades:
        assert isinstance(t, Trade)

    # We need to access the frame to use order indexing
    first = trades[trades.id[0]]  # taking the frame with first id in the list
    # CAREFUL : the frame has been reordered by ascending Trade.id field.
    # it just happen to be the same order, since Trade.id should follow time (= response order)...
    assert start_time < first.time_utc < end_time
    assert first.time_utc == datetime(
        year=2020,
        month=8,
        day=27,
        hour=10,
        minute=57,
        second=44,
        microsecond=478000,
        tzinfo=timezone.utc,  # stored as naive datetime into the frame, but retrieved as tz-aware...
    )
    assert first.symbol == "COTIBNB"
    assert first.id == 299229
    assert first.order_id == 18443055
    assert first.commission == Decimal("0.00066035")
    assert first.commission_asset == "BNB"
    assert first.is_best_match is True
    assert first.is_buyer is False
    assert first.is_maker is True
    assert first.order_list_id == -1  # TODO : should probably be None internally ?
    assert first.price == Decimal("0.00326100")
    assert first.qty == Decimal("300.000000000")
    assert first.quote_qty == Decimal("0.97830000")


if __name__ == "__main__":
    pytest.main(["-s", __file__, "--block-network"])
    # record run
    # pytest.main(['-s', __file__, '--with-keyfile', '--record-mode=new_episodes'])

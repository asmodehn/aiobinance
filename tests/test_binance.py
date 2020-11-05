from datetime import datetime, timezone

import pytest

# TODO : pytest-recording based test, just as in aiokraken...

from decimal import Decimal

import pytest
import aiobinance.binance
from aiobinance import OHLCV
from aiobinance.model import TradeFrame
from aiobinance.model.account import Account
from aiobinance.model.ohlcv import Candle
from aiobinance.model.trade import Trade


@pytest.mark.vcr(
    filter_headers=["X-MBX-APIKEY"], filter_query_parameters=["timestamp", "signature"]
)
def test_balance_from_binance(keyfile):
    """ get binance balances"""

    account = aiobinance.binance.balance_from_binance(
        key=keyfile.get("key"), secret=keyfile.get("secret")
    )

    assert isinstance(account, Account)
    assert account.accountType == "SPOT"
    assert len(account.balances) == 337  # TMP might change...
    assert account.buyerCommission == 0
    assert account.canDeposit is True
    assert account.canTrade is True
    assert account.canWithdraw is True
    assert account.makerCommission == 10
    assert "SPOT" in account.permissions
    assert account.sellerCommission == 0
    assert account.takerCommission == 10
    assert hasattr(account, "updateTime")


@pytest.mark.vcr(
    filter_headers=["X-MBX-APIKEY"], filter_query_parameters=["timestamp", "signature"]
)
def test_trades_from_binance(keyfile):
    """ get binance balances"""

    # TODO : use datetime in interface
    start_time = 1598524340551
    end_time = start_time + 24 * 3_600_000
    trades = aiobinance.binance.trades_from_binance(
        "COTIBNB",
        start_time=start_time,
        end_time=end_time,
        key=keyfile.get("key"),
        secret=keyfile.get("secret"),
    )

    assert isinstance(trades, TradeFrame)

    assert len(trades) == 17
    for t in trades:
        assert isinstance(t, Trade)

    first = trades[0]
    assert (
        datetime.fromtimestamp(start_time / 1000, tz=timezone.utc)
        < first.time
        < datetime.fromtimestamp(end_time / 1000, tz=timezone.utc)
    )
    assert first.time == datetime(
        year=2020,
        month=8,
        day=27,
        hour=10,
        minute=57,
        second=44,
        microsecond=478000,
        tzinfo=timezone.utc,
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


@pytest.mark.vcr
def test_price_from_binance(keyfile):
    """ get binance balances"""

    # TODO : use datetime in interface
    start_time = 1598524340551
    end_time = start_time + 24 * 3_600_000
    ohlcv = aiobinance.binance.price_from_binance(
        "COTIBNB", start_time=start_time, end_time=end_time
    )

    assert isinstance(ohlcv, OHLCV)

    assert len(ohlcv) == 480
    for c in ohlcv:
        assert isinstance(c, Candle)

    first = ohlcv[0]
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

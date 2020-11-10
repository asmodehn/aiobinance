import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

import pytest
from click.testing import CliRunner

from aiobinance.__main__ import cli
from aiobinance.config import BINANCE_API_KEYFILE


# Note : no cassette needed if we dont need to retrieve OHLC data(only required with html...)
def test_hummingbot():
    # make temporary file with hummingbot csv format
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as fp:
        fp.write(
            r"""Config File,Strategy,Exchange,Timestamp,Market,Base,Quote,Trade,Type,Price,Amount,Fee,Age,Order ID,Exchange Trade ID
conf_pure_mm_coti_bnb_binance.yml,pure_market_making,binance,1598524340551,COTIBNB,COTI,BNB,BUY,LIMIT_MAKER,0.003219,300.0,"{'percent': 0.001, 'flat_fees': []}",00:08:52,x-XEKWYICX-BCIBB1598523808006812,299167
conf_pure_mm_coti_bnb_binance.yml,pure_market_making,binance,1598525864613,COTIBNB,COTI,BNB,SELL,LIMIT_MAKER,0.003261,300.0,"{'percent': 0.001, 'flat_fees': []}",00:20:23,x-XEKWYICX-SCIBB1598524641006675,299229
conf_pure_mm_coti_bnb_binance.yml,pure_market_making,binance,1598526454594,COTIBNB,COTI,BNB,SELL,LIMIT_MAKER,0.003289,300.0,"{'percent': 0.001, 'flat_fees': []}",00:04:49,x-XEKWYICX-SCIBB1598526165003515,299244
conf_pure_mm_coti_bnb_binance.yml,pure_market_making,binance,1598526454743,COTIBNB,COTI,BNB,SELL,LIMIT_MAKER,0.00329,300.0,"{'percent': 0.001, 'flat_fees': []}",00:44:06,x-XEKWYICX-SCIBB1598523808007285,299246
"""
        )
        fp.seek(0)

    runner = CliRunner()
    result = runner.invoke(cli, f"hummingbot {fp.name}".split(), input="2")

    if result.exit_code == 0:
        assert (
            "|    | time                             | symbol   |     id |    price |   qty |   quote_qty |   commission | commission_asset   | is_buyer   | is_maker   | order_id   | order_list_id   | is_best_match   |"
            in result.output
        )
        assert (
            "|  0 | 2020-08-27 10:32:20.551000+00:00 | COTIBNB  | 299167 | 0.003219 |   300 |      0.9657 |    0.0009657 | BNB                | True       | True       |            |                 |                 |"
            in result.output
        )
        assert (
            "|  1 | 2020-08-27 10:57:44.613000+00:00 | COTIBNB  | 299229 | 0.003261 |   300 |      0.9783 |    0.0009783 | BNB                | False      | True       |            |                 |                 |"
            in result.output
        )
        assert (
            "|  2 | 2020-08-27 11:07:34.594000+00:00 | COTIBNB  | 299244 | 0.003289 |   300 |      0.9867 |    0.0009867 | BNB                | False      | True       |            |                 |                 |"
            in result.output
        )
        assert (
            "|  3 | 2020-08-27 11:07:34.743000+00:00 | COTIBNB  | 299246 | 0.00329  |   300 |      0.987  |    0.000987  | BNB                | False      | True       |            |                 |                 |"
            in result.output
        )
    else:
        raise result.exception


def test_auth():
    """ testing auth command depending on user's environment """
    runner = CliRunner()
    result = runner.invoke(cli, "auth".split(), input="2")
    # Result and output depends on the environment of the user running the tests
    if os.path.exists(BINANCE_API_KEYFILE):
        assert result.exit_code == 0
        assert "apikey: " in result.output
    else:
        assert result.exit_code == 1
        assert f"{BINANCE_API_KEYFILE} Not Found !" in result.output


def test_auth_verbose():

    """ testing auth --verbose command depending on user's environment """
    runner = CliRunner()
    result = runner.invoke(cli, "auth --verbose".split(), input="2")
    # Result and output depends on the environment of the user running the tests
    if os.path.exists(BINANCE_API_KEYFILE):
        assert result.exit_code == 0
        assert f"{BINANCE_API_KEYFILE}" in result.output
        assert "apikey: " in result.output
    else:
        assert result.exit_code == 1
        assert f"{BINANCE_API_KEYFILE} Not Found !" in result.output


@pytest.mark.vcr(
    filter_headers=["X-MBX-APIKEY"], filter_query_parameters=["timestamp", "signature"]
)
def test_balance(keyfile):

    """ testing balance command with --keyfile or from cassettes """
    runner = CliRunner()

    # passing keyfile so the results do not depend on environment (arguably too complex with 2 levels of envs)
    # but on how pytest is called to run the tests. We're testing the --apikey and --secret options at the same time.
    result = runner.invoke(
        cli,
        f"balance --apikey {keyfile.key} --secret {keyfile.secret}".split(),
        input="2",
    )

    if result.exit_code == 0:
        assert "accountType: SPOT" in result.output
        assert "canTrade: True" in result.output
        assert "canWithdraw: True" in result.output
        assert "canDeposit: True" in result.output

        assert "balances:" in result.output
        assert " - 0.02084500 ETH (free: 0.02084500, locked: 0E-8)" in result.output
        assert " - 12.83529493 BNB (free: 12.83529493, locked: 0E-8)" in result.output
        assert " - 86.40000000 XRP (free: 86.40000000, locked: 0E-8)" in result.output
        assert " - 208.93330180 EUR (free: 208.93330180, locked: 0E-8)" in result.output
        assert (
            " - 416.00000000 COTI (free: 416.00000000, locked: 0E-8)" in result.output
        )
        assert " - 0.94611754 SXP (free: 0.94611754, locked: 0E-8)" in result.output

        assert "updateTime: 2020-11-02 20:15:07.791000+00:00" in result.output
        assert "permissions: ['SPOT']" in result.output
        assert "makerCommission: 10" in result.output
        assert "takerCommission: 10" in result.output
    else:
        raise result.exception


@pytest.mark.vcr(
    filter_headers=["X-MBX-APIKEY"], filter_query_parameters=["timestamp", "signature"]
)
def test_trades(keyfile):
    """ testing trades command with --keyfile or from cassettes """

    start_time = datetime.fromtimestamp(1598524340551 / 1000, tz=timezone.utc)
    end_time = start_time + timedelta(days=1)

    runner = CliRunner()
    result = runner.invoke(
        cli,
        f"trades COTIBNB --from {start_time.strftime('%Y-%m-%d')} --to {end_time.strftime('%Y-%m-%d')} --apikey {keyfile.key} --secret {keyfile.secret}".split(),
        input="2",
    )

    if result.exit_code == 0:
        assert (
            "|    | time                             | symbol   |     id |    price |   qty |   quote_qty |   commission | commission_asset   | is_buyer   | is_maker   |   order_id |   order_list_id | is_best_match   |"
            in result.output
        )
        assert (
            "|  0 | 2020-08-27 10:32:20.409000+00:00 | COTIBNB  | 299167 | 0.003219 |   300 |    0.9657   |   0.00065495 | BNB                | True       | True       |   18441464 |              -1 | True            |"
            in result.output
        )
        assert (
            "|  1 | 2020-08-27 10:57:44.478000+00:00 | COTIBNB  | 299229 | 0.003261 |   300 |    0.9783   |   0.00066035 | BNB                | False      | True       |   18443055 |              -1 | True            |"
            in result.output
        )
        assert (
            "|  2 | 2020-08-27 11:07:34.459000+00:00 | COTIBNB  | 299244 | 0.003289 |   300 |    0.9867   |   0.00066602 | BNB                | False      | True       |   18446230 |              -1 | True            |"
            in result.output
        )
        assert (
            "|  3 | 2020-08-27 11:07:34.459000+00:00 | COTIBNB  | 299246 | 0.00329  |   300 |    0.987    |   0.00066622 | BNB                | False      | True       |   18441463 |              -1 | True            |"
            in result.output
        )
        assert (
            "|  4 | 2020-08-27 11:23:34.060000+00:00 | COTIBNB  | 299456 | 0.003285 |   300 |    0.9855   |   0.00068733 | BNB                | True       | True       |   18448574 |              -1 | True            |"
            in result.output
        )
        assert (
            "|  5 | 2020-08-27 11:37:23.670000+00:00 | COTIBNB  | 299815 | 0.003245 |   300 |    0.9735   |   0.00065593 | BNB                | True       | True       |   18454107 |              -1 | True            |"
            in result.output
        )
        assert (
            "|  6 | 2020-08-27 13:41:13.140000+00:00 | COTIBNB  | 300255 | 0.003209 |    61 |    0.195749 |   0.0001322  | BNB                | True       | True       |   18478551 |              -1 | True            |"
            in result.output
        )
        assert (
            "|  7 | 2020-08-27 13:41:22.243000+00:00 | COTIBNB  | 300256 | 0.003209 |    97 |    0.311273 |   0.00021023 | BNB                | True       | True       |   18478551 |              -1 | True            |"
            in result.output
        )
        assert (
            "|  8 | 2020-08-27 17:06:47.354000+00:00 | COTIBNB  | 300607 | 0.003125 |   300 |    0.9375   |   0.00063539 | BNB                | True       | True       |   18506959 |              -1 | True            |"
            in result.output
        )
    else:
        raise result.exception


@pytest.mark.vcr
def test_price(keyfile):

    """ testing price command with --keyfile or from cassettes """

    start_time = datetime.fromtimestamp(1598524340551 / 1000, tz=timezone.utc)
    end_time = start_time + timedelta(days=1)

    runner = CliRunner()
    result = runner.invoke(
        cli,
        f"price COTIBNB --from {start_time.strftime('%Y-%m-%d')} --to {end_time.strftime('%Y-%m-%d')}".split(),
        input="2",
    )

    if result.exit_code == 0:
        assert (
            "|     | open_time                 |     open |     high |      low |    close |   volume | close_time                       |        qav |   num_trades |   taker_base_vol |   taker_quote_vol |   is_best_match |"
            in result.output
        )
        assert (
            "|   0 | 2020-08-26 22:00:00+00:00 | 0.003472 | 0.003472 | 0.003468 | 0.003468 |     1962 | 2020-08-26 22:02:59.999000+00:00 |   6.8054   |            3 |                0 |          0        |               0 |"
            in result.output
        )
        # testing first and last line only...
        assert (
            "| 480 | 2020-08-27 22:00:00+00:00 | 0.003153 | 0.003153 | 0.003153 | 0.003153 |        0 | 2020-08-27 22:02:59.999000+00:00 |   0        |            0 |                0 |          0        |               0 |"
            in result.output
        )
    else:
        raise result.exception


if __name__ == "__main__":
    pytest.main(["-s", __file__, "--block-network"])
    # record run
    # pytest.main(['-s', __file__, '--with-keyfile', '--record-mode=new_episodes'])
